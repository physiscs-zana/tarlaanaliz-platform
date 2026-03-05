# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: get_pilot_available_slots.py dosyasının rolünü tanımlar.
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
class GetPilotAvailableSlotsRequest:
    actor_user_id: str
    correlation_id: str
    pilot_id: str
    start_date: date
    end_date: date


@dataclass(frozen=True, slots=True)
class PilotAvailableSlot:
    date: date
    remaining_capacity: int


@dataclass(frozen=True, slots=True)
class GetPilotAvailableSlotsResult:
    correlation_id: str
    pilot_id: str
    slots: tuple[PilotAvailableSlot, ...]


class PilotAvailabilityReadPort(Protocol):
    async def list_available_slots(
        self,
        *,
        pilot_id: str,
        start_date: date,
        end_date: date,
    ) -> list[PilotAvailableSlot]: ...


class AuthorizerPort(Protocol):
    async def can_view_pilot_slots(self, actor_user_id: str, pilot_id: str) -> bool: ...


class RateLimiterPort(Protocol):
    async def allow(self, *, actor_user_id: str, action: str) -> bool: ...


class AuditLoggerPort(Protocol):
    async def log_query(self, *, correlation_id: str, actor_user_id: str, query_name: str) -> None: ...


@dataclass(slots=True)
class GetPilotAvailableSlotsQuery:
    read_port: PilotAvailabilityReadPort
    authorizer: AuthorizerPort
    rate_limiter: RateLimiterPort
    audit_logger: AuditLoggerPort

    # KR-015: slot/capacity windows are explicit in query contract.
    async def execute(self, request: GetPilotAvailableSlotsRequest) -> GetPilotAvailableSlotsResult:
        if request.start_date > request.end_date:
            raise ValueError("start_date cannot be after end_date")

        if not await self.rate_limiter.allow(actor_user_id=request.actor_user_id, action="get_pilot_available_slots"):
            raise QueryRateLimitError("rate limit exceeded")
        if not await self.authorizer.can_view_pilot_slots(request.actor_user_id, request.pilot_id):
            raise QueryAuthzError("actor is not authorized")

        slots = await self.read_port.list_available_slots(
            pilot_id=request.pilot_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        await self.audit_logger.log_query(
            correlation_id=request.correlation_id,
            actor_user_id=request.actor_user_id,
            query_name="GetPilotAvailableSlotsQuery",
        )
        return GetPilotAvailableSlotsResult(
            correlation_id=request.correlation_id,
            pilot_id=request.pilot_id,
            slots=tuple(slots),
        )
