# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-015: Weather-block report and replan events are orchestrated here.
# KR-015-3A: Pilot sahada tek yetkili; admin doğrulama akışı kaldırılmıştır.
# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Weather Block raporu alma ve yeniden planlama.
Sorumluluk: Use-case orkestrasyonu; domain service + ports birleşimi; policy enforcement.
Girdi/Çıktı (Contract/DTO/Event): Girdi: API/Job/Worker tetiklemesi. Çıktı: DTO, event, state transition.
Güvenlik (RBAC/PII/Audit): RBAC burada; PII redaction; audit log; rate limit (gereken yerde).
Hata Modları (idempotency/retry/rate limit): 400/403/409/429/5xx mapping; retry-safe tasarım; idempotency key/hard gate’ler.
Observability (log fields/metrics/traces): correlation_id, latency, error_code; use-case metric sayaçları.
Testler: Unit + integration; kritik akış için e2e (özellikle ödeme/planlama/kalibrasyon).
Bağımlılıklar: Domain + ports + infra implementasyonları + event bus.
Notlar/SSOT: Contract-first (KR-081) ve kritik kapılar (KR-018/KR-033/KR-015) application katmanında enforce edilir.

NOTE: The Protocol classes and dataclasses defined below are APPLICATION-LAYER ports
and DTOs, intentionally distinct from core domain types (core.ports.messaging.EventBus,
etc.). The core EventBus is async/DomainEvent-based while these application-layer ports
use a simpler sync/string-based contract. An infrastructure adapter bridges between
these two abstractions at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


# Application-layer DTO — simplified projection for use-case orchestration.
@dataclass(frozen=True, slots=True)
class WeatherBlockReport:
    report_id: str
    mission_id: str
    pilot_id: str
    ts_ms: int
    reason: str
    evidence_uri: str | None = None


# Application-layer port — NOT the same as core.ports.persistence.*Repository.
class WeatherBlockRepository(Protocol):
    def create(self, report: WeatherBlockReport) -> None: ...


# Application-layer port — sync/string-based, distinct from core.ports.messaging.EventBus
# (which is async/DomainEvent-based). Bridged via an infrastructure adapter.
class EventBus(Protocol):
    def publish(self, event_name: str, payload: dict[str, Any], *, correlation_id: str) -> None: ...


class WeatherBlockService:
    def __init__(self, repo: WeatherBlockRepository, bus: EventBus) -> None:
        self._repo = repo
        self._bus = bus

    def report(self, *, report: WeatherBlockReport, correlation_id: str) -> None:
        self._repo.create(report)
        self._bus.publish(
            "weather_block.reported",
            {"report_id": report.report_id, "mission_id": report.mission_id},
            correlation_id=correlation_id,
        )

