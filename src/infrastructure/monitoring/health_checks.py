# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/infrastructure/monitoring/health_checks.py
# DESC: Uygulama sağlık kontrolü bileşeni.
"""
Health Checks: uygulama ve bağımlılık sağlık kontrolü.

Amaç: Tüm dış bağımlılıkların (PostgreSQL, Redis, RabbitMQ, S3) ve
  uygulama servislerinin erişilebilirliğini kontrol eder. Kubernetes
  liveness/readiness probe'ları ve yük dengeleyici kontrolleri için
  birleşik sağlık durumu sunar.

Sorumluluk: Bağımlılık sağlığı kontrolü, birleşik durum raporlama.

Güvenlik (RBAC/PII/Audit):
  Health endpoint'i hassas bilgi döndürmez (sadece status + latency).

Observability (log fields/metrics/traces):
  check_name, status, latency_ms, error (varsa).

Testler: Unit test (mock bağımlılıklar), integration test (gerçek bağımlılıklar).
Bağımlılıklar: Settings, structlog, asyncio.
Notlar/SSOT: Tek referans: tarlaanaliz_platform_tree v3.2.2 FINAL.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Optional, cast

import structlog

from src.infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)


class HealthStatus(str, Enum):
    """Sağlık durumu değerleri."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True)
class CheckResult:
    """Tek bir sağlık kontrolünün sonucu."""

    name: str
    status: HealthStatus
    latency_ms: float
    detail: str = ""
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict."""
        result: dict[str, Any] = {
            "name": self.name,
            "status": self.status.value,
            "latency_ms": round(self.latency_ms, 2),
        }
        if self.detail:
            result["detail"] = self.detail
        if self.error:
            result["error"] = self.error
        return result


@dataclass(frozen=True)
class HealthReport:
    """Birleşik sağlık raporu."""

    status: HealthStatus
    checks: list[CheckResult]
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict."""
        return {
            "status": self.status.value,
            "checks": [c.to_dict() for c in self.checks],
            "checked_at": self.checked_at.isoformat(),
        }


# Check fonksiyonu tipi: async callable, bool döner (True=sağlıklı)
HealthCheckFn = Callable[[], Awaitable[bool]]


class HealthChecker:
    """Birleşik sağlık kontrolü yöneticisi.

    Kayıtlı tüm sağlık kontrollerini çalıştırır ve birleşik
    sonuç üretir. Kubernetes liveness/readiness probe'ları ve
    yük dengeleyici kontrolleri bu sınıfı kullanır.

    Özellikler:
      - Pluggable check fonksiyonları (register/unregister)
      - Paralel veya sıralı kontrol
      - Birleşik durum: tümü healthy -> HEALTHY,
        en az biri unhealthy -> DEGRADED, hiçbiri ulaşılamaz -> UNHEALTHY
      - Check bazında timeout ve latency ölçümü

    Kullanım:
        checker = HealthChecker(settings)
        checker.register("database", db_health_check)
        checker.register("rabbitmq", rabbitmq_health_check)
        report = await checker.run_all()
    """

    def __init__(
        self,
        settings: Settings,
        *,
        check_timeout_seconds: float = 5.0,
    ) -> None:
        self._settings = settings
        self._check_timeout = check_timeout_seconds
        self._checks: dict[str, HealthCheckFn] = {}

    def register(self, name: str, check_fn: HealthCheckFn) -> None:
        """Sağlık kontrolü kaydet.

        Args:
            name: Kontrol adı (ör: "database", "rabbitmq").
            check_fn: Async fonksiyon, True döndürmeli (sağlıklı).
        """
        self._checks[name] = check_fn
        logger.debug("health_check_registered", name=name)

    def unregister(self, name: str) -> None:
        """Sağlık kontrolünü kaldır.

        Args:
            name: Kaldırılacak kontrol adı.
        """
        self._checks.pop(name, None)

    async def run_check(self, name: str) -> CheckResult:
        """Tek bir sağlık kontrolünü çalıştır.

        Args:
            name: Kontrol adı.

        Returns:
            CheckResult: Kontrol sonucu.
        """
        import asyncio

        check_fn = self._checks.get(name)
        if check_fn is None:
            return CheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=0,
                error=f"Kontrol bulunamadı: {name}",
            )

        start_time = time.monotonic()

        try:
            is_healthy = await asyncio.wait_for(
                check_fn(),
                timeout=self._check_timeout,
            )
            latency_ms = (time.monotonic() - start_time) * 1000

            status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY

            return CheckResult(
                name=name,
                status=status,
                latency_ms=latency_ms,
            )

        except asyncio.TimeoutError:
            latency_ms = (time.monotonic() - start_time) * 1000
            logger.warning(
                "health_check_timeout",
                name=name,
                timeout_seconds=self._check_timeout,
            )
            return CheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                error="Timeout",
            )

        except Exception as exc:
            latency_ms = (time.monotonic() - start_time) * 1000
            logger.error(
                "health_check_error",
                name=name,
                error=str(exc),
            )
            return CheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                error=str(exc),
            )

    async def run_all(self) -> HealthReport:
        """Tüm kayıtlı kontrolleri çalıştır ve birleşik rapor döner.

        Returns:
            HealthReport: Birleşik sağlık raporu.
        """
        import asyncio

        if not self._checks:
            return HealthReport(
                status=HealthStatus.HEALTHY,
                checks=[],
            )

        # Tüm kontrolleri paralel çalıştır
        tasks = [self.run_check(name) for name in self._checks]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Birleşik durum belirle
        unhealthy_count = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)

        if unhealthy_count == 0:
            overall_status = HealthStatus.HEALTHY
        elif unhealthy_count < len(results):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNHEALTHY

        report = HealthReport(
            status=overall_status,
            checks=list(results),
        )

        logger.info(
            "health_check_completed",
            status=overall_status.value,
            total_checks=len(results),
            unhealthy_count=unhealthy_count,
        )

        return report

    async def check_database(self) -> bool:
        """PostgreSQL bağlantı kontrolü."""
        try:
            import asyncpg

            conn = await asyncpg.connect(
                host=self._settings.db_host,
                port=self._settings.db_port,
                user=self._settings.db_user,
                password=self._settings.db_password.get_secret_value(),
                database=self._settings.db_name,
                timeout=self._check_timeout,
            )
            try:
                await conn.fetchval("SELECT 1")
                return True
            finally:
                await conn.close()
        except Exception as exc:
            logger.warning("health_check_database_failed", error=str(exc))
            return False

    async def check_redis(self) -> bool:
        """Redis bağlantı kontrolü."""
        try:
            import redis.asyncio as aioredis

            client = cast(Any, aioredis).from_url(
                self._settings.redis_url,
                socket_timeout=self._check_timeout,
            )
            try:
                result = await client.ping()
                return bool(result)
            finally:
                await client.aclose()
        except Exception as exc:
            logger.warning("health_check_redis_failed", error=str(exc))
            return False

    async def check_rabbitmq(self) -> bool:
        """RabbitMQ bağlantı kontrolü."""
        try:
            import aio_pika

            connection = await aio_pika.connect_robust(
                self._settings.rabbitmq_url,
                timeout=self._check_timeout,
            )
            try:
                return not connection.is_closed
            finally:
                await connection.close()
        except Exception as exc:
            logger.warning("health_check_rabbitmq_failed", error=str(exc))
            return False

    async def check_weather_api(self) -> bool:
        """Open-Meteo API erişilebilirlik kontrolü (PII göndermez)."""
        try:
            from src.infrastructure.external.weather_api_adapter import WeatherAPIAdapter

            adapter = WeatherAPIAdapter(self._settings)
            return await adapter.health_check()
        except Exception as exc:
            logger.warning("health_check_weather_api_failed", error=str(exc))
            return False

    def register_default_checks(self) -> None:
        """Varsayılan bağımlılık kontrollerini kaydet.

        PostgreSQL, Redis, RabbitMQ ve Open-Meteo kontrolleri eklenir.
        """
        self.register("database", self.check_database)
        self.register("redis", self.check_redis)
        self.register("rabbitmq", self.check_rabbitmq)
        self.register("weather_api", self.check_weather_api)
