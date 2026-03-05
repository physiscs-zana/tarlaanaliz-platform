# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Expert review detay query'si.
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
from datetime import datetime
from typing import Protocol


class QueryAuthzError(PermissionError):
    pass


class QueryNotFoundError(LookupError):
    pass


class QueryRateLimitError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GetExpertReviewDetailsRequest:
    actor_user_id: str
    correlation_id: str
    review_id: str


@dataclass(frozen=True, slots=True)
class GetExpertReviewDetailsResult:
    correlation_id: str
    review_id: str
    mission_id: str
    expert_id: str
    status: str
    verdict: str | None
    assigned_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class ExpertReviewDetailsReadPort(Protocol):
    async def get_by_id(self, review_id: str) -> GetExpertReviewDetailsResult | None: ...


class AuthorizerPort(Protocol):
    async def can_view_expert_review(self, actor_user_id: str, review_id: str) -> bool: ...


class RateLimiterPort(Protocol):
    async def allow(self, *, actor_user_id: str, action: str) -> bool: ...


class AuditLoggerPort(Protocol):
    async def log_query(self, *, correlation_id: str, actor_user_id: str, query_name: str) -> None: ...


@dataclass(slots=True)
class GetExpertReviewDetailsQuery:
    read_port: ExpertReviewDetailsReadPort
    authorizer: AuthorizerPort
    rate_limiter: RateLimiterPort
    audit_logger: AuditLoggerPort

    async def execute(self, request: GetExpertReviewDetailsRequest) -> GetExpertReviewDetailsResult:
        if not await self.rate_limiter.allow(actor_user_id=request.actor_user_id, action="get_expert_review_details"):
            raise QueryRateLimitError("rate limit exceeded")
        if not await self.authorizer.can_view_expert_review(request.actor_user_id, request.review_id):
            raise QueryAuthzError("actor is not authorized")

        result = await self.read_port.get_by_id(request.review_id)
        if result is None:
            raise QueryNotFoundError("expert review not found")

        await self.audit_logger.log_query(
            correlation_id=request.correlation_id,
            actor_user_id=request.actor_user_id,
            query_name="GetExpertReviewDetailsQuery",
        )
        return GetExpertReviewDetailsResult(
            correlation_id=request.correlation_id,
            review_id=result.review_id,
            mission_id=result.mission_id,
            expert_id=result.expert_id,
            status=result.status,
            verdict=result.verdict,
            assigned_at=result.assigned_at,
            started_at=result.started_at,
            completed_at=result.completed_at,
        )
