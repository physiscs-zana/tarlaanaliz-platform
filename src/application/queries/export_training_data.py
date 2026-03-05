# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Training data export query'si.
Sorumluluk: Read use-case (CQRS query): RBAC, filtreleme/pagination, projection/DTO üretimi.
Girdi/Çıktı (Contract/DTO/Event): Girdi: API/Job/Worker tetiklemesi. Çıktı: DTO, event, state transition.
Güvenlik (RBAC/PII/Audit): RBAC burada; PII redaction; audit log; rate limit (gereken yerde).
Hata Modları (idempotency/retry/rate limit): 400/403/409/429/5xx mapping; retry-safe tasarım; idempotency key/hard gate’ler.
Observability (log fields/metrics/traces): correlation_id, latency, error_code; use-case metric sayaçları.
Testler: Unit + integration; kritik akış için e2e (özellikle ödeme/planlama/kalibrasyon).
Bağımlılıklar: Domain + ports + infra implementasyonları + event bus.
Notlar/SSOT: Contract-first (KR-081) ve kritik kapılar (KR-018/KR-033/KR-015) application katmanında enforce edilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


class QueryAuthzError(PermissionError):
    """Authorization failure for query execution."""


class QueryRateLimitError(RuntimeError):
    """Rate-limit hard fail for query execution."""


@dataclass(frozen=True, slots=True)
class ExportTrainingDataRequest:
    actor_user_id: str
    correlation_id: str
    format: str
    page: int = 1
    page_size: int = 100


@dataclass(frozen=True, slots=True)
class TrainingExportRow:
    sample_id: str
    mission_id: str
    field_id: str
    label: str | None
    captured_at: datetime
    payload_uri: str


@dataclass(frozen=True, slots=True)
class ExportTrainingDataResult:
    correlation_id: str
    format: str
    page: int
    page_size: int
    total: int
    items: tuple[TrainingExportRow, ...]
    exported_at: datetime


class TrainingExportReadPort(Protocol):
    async def fetch_training_samples(
        self,
        *,
        page: int,
        page_size: int,
        format: str,
    ) -> tuple[list[TrainingExportRow], int]: ...


class AuthorizerPort(Protocol):
    async def can_export_training_data(self, actor_user_id: str) -> bool: ...


class RateLimiterPort(Protocol):
    async def allow(self, *, actor_user_id: str, action: str) -> bool: ...


class AuditLoggerPort(Protocol):
    async def log_query(self, *, correlation_id: str, actor_user_id: str, query_name: str) -> None: ...


class ClockPort(Protocol):
    def now(self) -> datetime: ...


@dataclass(slots=True)
class ExportTrainingDataQuery:
    read_port: TrainingExportReadPort
    authorizer: AuthorizerPort
    rate_limiter: RateLimiterPort
    audit_logger: AuditLoggerPort
    clock: ClockPort

    # KR-081: stable request/result shape.
    async def execute(self, request: ExportTrainingDataRequest) -> ExportTrainingDataResult:
        if request.page <= 0 or request.page_size <= 0:
            raise ValueError("page and page_size must be positive")

        if not await self.rate_limiter.allow(actor_user_id=request.actor_user_id, action="export_training_data"):
            raise QueryRateLimitError("rate limit exceeded")

        if not await self.authorizer.can_export_training_data(request.actor_user_id):
            raise QueryAuthzError("actor is not authorized")

        rows, total = await self.read_port.fetch_training_samples(
            page=request.page,
            page_size=request.page_size,
            format=request.format,
        )
        await self.audit_logger.log_query(
            correlation_id=request.correlation_id,
            actor_user_id=request.actor_user_id,
            query_name="ExportTrainingDataQuery",
        )
        now = self.clock.now()
        return ExportTrainingDataResult(
            correlation_id=request.correlation_id,
            format=request.format,
            page=request.page,
            page_size=request.page_size,
            total=total,
            items=tuple(rows),
            exported_at=now if now.tzinfo else now.replace(tzinfo=timezone.utc),
        )
