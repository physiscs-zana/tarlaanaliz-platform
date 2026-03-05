# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Field detay query'si.
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
from decimal import Decimal
from typing import Protocol


class QueryAuthzError(PermissionError):
    pass


class QueryNotFoundError(LookupError):
    pass


class QueryRateLimitError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GetFieldDetailsRequest:
    actor_user_id: str
    correlation_id: str
    field_id: str


@dataclass(frozen=True, slots=True)
class GetFieldDetailsResult:
    correlation_id: str
    field_id: str
    owner_user_id: str
    province: str
    district: str
    village: str
    ada: str
    parsel: str
    area_m2: Decimal
    crop_type: str | None
    status: str
    updated_at: datetime


class FieldDetailsReadPort(Protocol):
    async def get_by_id(self, field_id: str) -> GetFieldDetailsResult | None: ...


class AuthorizerPort(Protocol):
    async def can_view_field(self, actor_user_id: str, field_id: str) -> bool: ...


class RateLimiterPort(Protocol):
    async def allow(self, *, actor_user_id: str, action: str) -> bool: ...


class AuditLoggerPort(Protocol):
    async def log_query(self, *, correlation_id: str, actor_user_id: str, query_name: str) -> None: ...


@dataclass(slots=True)
class GetFieldDetailsQuery:
    read_port: FieldDetailsReadPort
    authorizer: AuthorizerPort
    rate_limiter: RateLimiterPort
    audit_logger: AuditLoggerPort

    async def execute(self, request: GetFieldDetailsRequest) -> GetFieldDetailsResult:
        if not await self.rate_limiter.allow(actor_user_id=request.actor_user_id, action="get_field_details"):
            raise QueryRateLimitError("rate limit exceeded")
        if not await self.authorizer.can_view_field(request.actor_user_id, request.field_id):
            raise QueryAuthzError("actor is not authorized")

        result = await self.read_port.get_by_id(request.field_id)
        if result is None:
            raise QueryNotFoundError("field not found")

        await self.audit_logger.log_query(
            correlation_id=request.correlation_id,
            actor_user_id=request.actor_user_id,
            query_name="GetFieldDetailsQuery",
        )
        return GetFieldDetailsResult(
            correlation_id=request.correlation_id,
            field_id=result.field_id,
            owner_user_id=result.owner_user_id,
            province=result.province,
            district=result.district,
            village=result.village,
            ada=result.ada,
            parsel=result.parsel,
            area_m2=result.area_m2,
            crop_type=result.crop_type,
            status=result.status,
            updated_at=result.updated_at,
        )
