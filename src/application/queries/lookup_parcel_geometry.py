# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: ParcelRef → Geometry lookup (TKGM/MEGSİS port'u üzerinden).
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
from decimal import Decimal
from typing import Any, Protocol

from src.core.domain.value_objects.parcel_ref import ParcelRef
from src.core.ports.external.parcel_geometry_provider import ParcelGeometryProvider


class QueryValidationError(ValueError):
    pass


class QueryAuthzError(PermissionError):
    pass


class QueryNotFoundError(LookupError):
    pass


class QueryConflictError(RuntimeError):
    pass


class QueryRateLimitError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LookupParcelGeometryRequest:
    actor_user_id: str
    correlation_id: str
    province: str
    district: str
    village: str
    ada: str
    parsel: str

    def __post_init__(self) -> None:
        if not self.actor_user_id:
            raise QueryValidationError("actor_user_id is required")
        if not self.correlation_id:
            raise QueryValidationError("correlation_id is required")
        if not self.province or not self.district or not self.village or not self.ada or not self.parsel:
            raise QueryValidationError("province, district, village, ada and parsel are required")


@dataclass(frozen=True, slots=True)
class LookupParcelGeometryResult:
    correlation_id: str
    parcel_ref: str
    area_m2: Decimal
    coordinate_system: str
    geometry: dict[str, Any]


class AuthorizerPort(Protocol):
    async def can_lookup_parcel_geometry(self, actor_user_id: str) -> bool: ...


class RateLimiterPort(Protocol):
    async def allow(self, *, actor_user_id: str, action: str) -> bool: ...


class AuditLoggerPort(Protocol):
    async def log_query(self, *, correlation_id: str, actor_user_id: str, query_name: str) -> None: ...


@dataclass(slots=True)
class LookupParcelGeometryQuery:
    tkgm_provider: ParcelGeometryProvider
    authorizer: AuthorizerPort
    rate_limiter: RateLimiterPort
    audit_logger: AuditLoggerPort

    # KR-081: request/result contract is explicit and stable.
    async def execute(self, request: LookupParcelGeometryRequest) -> LookupParcelGeometryResult:
        if not await self.rate_limiter.allow(actor_user_id=request.actor_user_id, action="lookup_parcel_geometry"):
            raise QueryRateLimitError("rate limit exceeded")
        if not await self.authorizer.can_lookup_parcel_geometry(request.actor_user_id):
            raise QueryAuthzError("actor is not authorized")

        # KR-081: lookup uses external geometry port contract.
        parcel = ParcelRef(
            province=request.province,
            district=request.district,
            village=request.village,
            ada=request.ada,
            parsel=request.parsel,
        )
        geometry = await self.tkgm_provider.get_geometry(parcel)
        if geometry is None:
            raise QueryNotFoundError("parcel geometry not found")
        if geometry.area_m2 <= 0:
            raise QueryConflictError("parcel geometry area_m2 must be positive")

        await self.audit_logger.log_query(
            correlation_id=request.correlation_id,
            actor_user_id=request.actor_user_id,
            query_name="LookupParcelGeometryQuery",
        )
        return LookupParcelGeometryResult(
            correlation_id=request.correlation_id,
            parcel_ref=geometry.parcel_ref.composite_key,
            area_m2=geometry.area_m2,
            coordinate_system=geometry.coordinate_system,
            geometry=geometry.geometry,
        )
