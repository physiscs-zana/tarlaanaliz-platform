# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: get_mission_timeline.py dosyasının rolünü tanımlar.
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
class GetMissionTimelineRequest:
    actor_user_id: str
    correlation_id: str
    mission_id: str


@dataclass(frozen=True, slots=True)
class MissionTimelineItem:
    event_type: str
    occurred_at: datetime
    status: str | None
    note: str | None


@dataclass(frozen=True, slots=True)
class GetMissionTimelineResult:
    correlation_id: str
    mission_id: str
    items: tuple[MissionTimelineItem, ...]


class MissionTimelineReadPort(Protocol):
    async def get_timeline(self, mission_id: str) -> list[MissionTimelineItem]: ...


class AuthorizerPort(Protocol):
    async def can_view_mission(self, actor_user_id: str, mission_id: str) -> bool: ...


class RateLimiterPort(Protocol):
    async def allow(self, *, actor_user_id: str, action: str) -> bool: ...


class AuditLoggerPort(Protocol):
    async def log_query(self, *, correlation_id: str, actor_user_id: str, query_name: str) -> None: ...


@dataclass(slots=True)
class GetMissionTimelineQuery:
    read_port: MissionTimelineReadPort
    authorizer: AuthorizerPort
    rate_limiter: RateLimiterPort
    audit_logger: AuditLoggerPort

    async def execute(self, request: GetMissionTimelineRequest) -> GetMissionTimelineResult:
        if not await self.rate_limiter.allow(actor_user_id=request.actor_user_id, action="get_mission_timeline"):
            raise QueryRateLimitError("rate limit exceeded")
        if not await self.authorizer.can_view_mission(request.actor_user_id, request.mission_id):
            raise QueryAuthzError("actor is not authorized")

        items = await self.read_port.get_timeline(request.mission_id)
        if not items:
            raise QueryNotFoundError("mission timeline not found")

        await self.audit_logger.log_query(
            correlation_id=request.correlation_id,
            actor_user_id=request.actor_user_id,
            query_name="GetMissionTimelineQuery",
        )
        return GetMissionTimelineResult(
            correlation_id=request.correlation_id,
            mission_id=request.mission_id,
            items=tuple(items),
        )
