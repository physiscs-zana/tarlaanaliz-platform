# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: get_expert_queue_stats.py dosyasının rolünü tanımlar.
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
from typing import Protocol


class QueryAuthzError(PermissionError):
    pass


class QueryRateLimitError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GetExpertQueueStatsRequest:
    actor_user_id: str
    correlation_id: str


@dataclass(frozen=True, slots=True)
class GetExpertQueueStatsResult:
    correlation_id: str
    pending_count: int
    in_progress_count: int
    completed_today_count: int
    avg_completion_minutes: float | None


class ExpertQueueStatsReadPort(Protocol):
    async def get_stats(self) -> GetExpertQueueStatsResult: ...


class AuthorizerPort(Protocol):
    async def can_view_expert_queue_stats(self, actor_user_id: str) -> bool: ...


class RateLimiterPort(Protocol):
    async def allow(self, *, actor_user_id: str, action: str) -> bool: ...


class AuditLoggerPort(Protocol):
    async def log_query(self, *, correlation_id: str, actor_user_id: str, query_name: str) -> None: ...


@dataclass(slots=True)
class GetExpertQueueStatsQuery:
    read_port: ExpertQueueStatsReadPort
    authorizer: AuthorizerPort
    rate_limiter: RateLimiterPort
    audit_logger: AuditLoggerPort

    async def execute(self, request: GetExpertQueueStatsRequest) -> GetExpertQueueStatsResult:
        if not await self.rate_limiter.allow(actor_user_id=request.actor_user_id, action="get_expert_queue_stats"):
            raise QueryRateLimitError("rate limit exceeded")
        if not await self.authorizer.can_view_expert_queue_stats(request.actor_user_id):
            raise QueryAuthzError("actor is not authorized")

        result = await self.read_port.get_stats()
        await self.audit_logger.log_query(
            correlation_id=request.correlation_id,
            actor_user_id=request.actor_user_id,
            query_name="GetExpertQueueStatsQuery",
        )
        return GetExpertQueueStatsResult(
            correlation_id=request.correlation_id,
            pending_count=result.pending_count,
            in_progress_count=result.in_progress_count,
            completed_today_count=result.completed_today_count,
            avg_completion_minutes=result.avg_completion_minutes,
        )
