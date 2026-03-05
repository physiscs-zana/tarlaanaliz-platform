# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Subscription detay query'si.
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


class QueryConflictError(RuntimeError):
    pass


class QueryRateLimitError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GetSubscriptionDetailsRequest:
    actor_user_id: str
    correlation_id: str
    subscription_id: str


@dataclass(frozen=True, slots=True)
class GetSubscriptionDetailsResult:
    correlation_id: str
    subscription_id: str
    user_id: str
    field_id: str
    status: str
    next_due_at: datetime
    last_payment_intent_id: str | None


class SubscriptionDetailsReadPort(Protocol):
    async def get_by_id(self, subscription_id: str) -> GetSubscriptionDetailsResult | None: ...


class PaymentConsistencyReadPort(Protocol):
    async def exists_intent(self, payment_intent_id: str) -> bool: ...


class AuthorizerPort(Protocol):
    async def can_view_subscription(self, actor_user_id: str, subscription_id: str) -> bool: ...


class RateLimiterPort(Protocol):
    async def allow(self, *, actor_user_id: str, action: str) -> bool: ...


class AuditLoggerPort(Protocol):
    async def log_query(self, *, correlation_id: str, actor_user_id: str, query_name: str) -> None: ...


@dataclass(slots=True)
class GetSubscriptionDetailsQuery:
    read_port: SubscriptionDetailsReadPort
    payment_read_port: PaymentConsistencyReadPort
    authorizer: AuthorizerPort
    rate_limiter: RateLimiterPort
    audit_logger: AuditLoggerPort

    async def execute(self, request: GetSubscriptionDetailsRequest) -> GetSubscriptionDetailsResult:
        if not await self.rate_limiter.allow(actor_user_id=request.actor_user_id, action="get_subscription_details"):
            raise QueryRateLimitError("rate limit exceeded")
        if not await self.authorizer.can_view_subscription(request.actor_user_id, request.subscription_id):
            raise QueryAuthzError("actor is not authorized")

        result = await self.read_port.get_by_id(request.subscription_id)
        if result is None:
            raise QueryNotFoundError("subscription not found")

        # KR-033: paid-state consistency requires valid payment intent linkage.
        if result.status == "ACTIVE" and result.last_payment_intent_id:
            if not await self.payment_read_port.exists_intent(result.last_payment_intent_id):
                raise QueryConflictError("subscription references missing payment intent")

        await self.audit_logger.log_query(
            correlation_id=request.correlation_id,
            actor_user_id=request.actor_user_id,
            query_name="GetSubscriptionDetailsQuery",
        )
        return GetSubscriptionDetailsResult(
            correlation_id=request.correlation_id,
            subscription_id=result.subscription_id,
            user_id=result.user_id,
            field_id=result.field_id,
            status=result.status,
            next_due_at=result.next_due_at,
            last_payment_intent_id=result.last_payment_intent_id,
        )
