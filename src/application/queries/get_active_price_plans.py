# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: get_active_price_plans.py dosyasının rolünü tanımlar.
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
from datetime import date
from typing import Protocol


class QueryAuthzError(PermissionError):
    pass


class QueryRateLimitError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GetActivePricePlansRequest:
    actor_user_id: str
    correlation_id: str
    as_of: date


@dataclass(frozen=True, slots=True)
class PricePlanItem:
    price_snapshot_id: str
    crop_type: str
    analysis_type: str
    amount_kurus: int
    currency: str
    effective_date: date
    effective_until: date | None


@dataclass(frozen=True, slots=True)
class GetActivePricePlansResult:
    correlation_id: str
    as_of: date
    items: tuple[PricePlanItem, ...]


class PricePlanReadPort(Protocol):
    async def list_active(self, *, as_of: date) -> list[PricePlanItem]: ...


class AuthorizerPort(Protocol):
    async def can_view_price_plans(self, actor_user_id: str) -> bool: ...


class RateLimiterPort(Protocol):
    async def allow(self, *, actor_user_id: str, action: str) -> bool: ...


class AuditLoggerPort(Protocol):
    async def log_query(self, *, correlation_id: str, actor_user_id: str, query_name: str) -> None: ...


@dataclass(slots=True)
class GetActivePricePlansQuery:
    read_port: PricePlanReadPort
    authorizer: AuthorizerPort
    rate_limiter: RateLimiterPort
    audit_logger: AuditLoggerPort

    # KR-081: stable result shape for presentation mapping.
    async def execute(self, request: GetActivePricePlansRequest) -> GetActivePricePlansResult:
        if not await self.rate_limiter.allow(actor_user_id=request.actor_user_id, action="get_active_price_plans"):
            raise QueryRateLimitError("rate limit exceeded")
        if not await self.authorizer.can_view_price_plans(request.actor_user_id):
            raise QueryAuthzError("actor is not authorized")

        items = await self.read_port.list_active(as_of=request.as_of)
        await self.audit_logger.log_query(
            correlation_id=request.correlation_id,
            actor_user_id=request.actor_user_id,
            query_name="GetActivePricePlansQuery",
        )
        return GetActivePricePlansResult(
            correlation_id=request.correlation_id,
            as_of=request.as_of,
            items=tuple(items),
        )
