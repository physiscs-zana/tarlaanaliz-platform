# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-028: Mission lifecycle transitions — PLANNED→ASSIGNED→ACKED→FLOWN→UPLOADED→ANALYZING→DONE
# KR-033: PLANNED→ASSIGNED geçişi için payment_intent.status==PAID hard gate (caller sorumluluğu)
"""
Amaç: Mission yaşam döngüsü yönetimi.
Sorumluluk: Use-case orkestrasyonu; domain service + ports birleşimi; policy enforcement.
Girdi/Çıktı (Contract/DTO/Event): Girdi: API/Job/Worker tetiklemesi. Çıktı: DTO, event, state transition.
Güvenlik (RBAC/PII/Audit): RBAC burada; PII redaction; audit log; rate limit (gereken yerde).
Hata Modları (idempotency/retry/rate limit): 400/403/409/429/5xx mapping; retry-safe tasarım; idempotency key/hard gate'ler.
Observability (log fields/metrics/traces): correlation_id, latency, error_code; use-case metric sayaçları.
Testler: Unit + integration; kritik akış için e2e (özellikle ödeme/planlama/kalibrasyon).
Bağımlılıklar: Domain + ports + infra implementasyonları + event bus.
Notlar/SSOT: Contract-first (KR-081) ve kritik kapılar (KR-018/KR-033/KR-015) application katmanında enforce edilir.

NOTE: The Protocol classes and dataclasses defined below are APPLICATION-LAYER ports
and DTOs, intentionally distinct from core domain types (core.ports.messaging.EventBus,
core.domain.entities.Mission, etc.). The core EventBus is async/DomainEvent-based while
these application-layer ports use a simpler sync/string-based contract. An infrastructure
adapter bridges between these two abstractions at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


# Application-layer DTO — simplified projection of core.domain.entities.Mission.
# Uses str IDs (not UUID) and a flat structure for use-case orchestration.
@dataclass(frozen=True, slots=True)
class Mission:
    mission_id: str
    field_id: str
    status: str
    pilot_id: str | None = None
    scheduled_ts_ms: int | None = None


# Application-layer port — NOT the same as core.ports.persistence.*Repository.
class MissionRepository(Protocol):
    def get(self, mission_id: str) -> Mission | None: ...

    def update(self, mission: Mission) -> None: ...


# Application-layer port — sync/string-based, distinct from core.ports.messaging.EventBus
# (which is async/DomainEvent-based). Bridged via an infrastructure adapter.
class EventBus(Protocol):
    def publish(self, event_name: str, payload: dict[str, Any], *, correlation_id: str) -> None: ...


class MissionLifecycleManager:
    def __init__(self, repo: MissionRepository, bus: EventBus) -> None:
        self._repo = repo
        self._bus = bus

    def transition(self, *, mission_id: str, to_status: str, correlation_id: str, **patch: Any) -> Mission:
        mission = self._repo.get(mission_id)
        if mission is None:
            raise ValueError("mission not found")

        # KR-028: SSOT v1.2.0 durum makinesi (uppercase)
        # KR-033: PLANNED→ASSIGNED geçişi sadece payment_intent.status==PAID ise yapılabilir;
        #         bu gate caller (mission_service.py) tarafından enforce edilir.
        allowed: dict[str, set[str]] = {
            "PLANNED": {"ASSIGNED", "CANCELLED"},
            "ASSIGNED": {"ACKED", "CANCELLED"},
            "ACKED": {"FLOWN", "CANCELLED"},
            "FLOWN": {"UPLOADED"},
            "UPLOADED": {"ANALYZING"},
            "ANALYZING": {"DONE", "FAILED"},
            "DONE": set(),
            "FAILED": set(),
            "CANCELLED": set(),
        }
        if to_status not in allowed.get(mission.status, set()):
            raise ValueError(f"invalid transition {mission.status} -> {to_status}")

        updated = Mission(
            mission_id=mission.mission_id,
            field_id=mission.field_id,
            status=to_status,
            pilot_id=patch.get("pilot_id", mission.pilot_id),
            scheduled_ts_ms=patch.get("scheduled_ts_ms", mission.scheduled_ts_ms),
        )
        self._repo.update(updated)
        self._bus.publish(
            "mission.status_changed",
            {"mission_id": mission_id, "from": mission.status, "to": to_status},
            correlation_id=correlation_id,
        )
        return updated
