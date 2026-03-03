# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-081: Mission command models are explicit and validated at the application boundary.
# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Mission orkestrasyon servisi.
Sorumluluk: Use-case orkestrasyonu; domain service + ports birleşimi; policy enforcement.
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
from typing import Any, Protocol

from .mission_lifecycle_manager import Mission, MissionLifecycleManager


class MissionRepository(Protocol):
    def create(self, mission: Mission) -> None: ...


class EventBus(Protocol):
    def publish(self, event_name: str, payload: dict[str, Any], *, correlation_id: str) -> None: ...


@dataclass(frozen=True, slots=True)
class CreateMissionRequest:
    mission_id: str
    field_id: str


class MissionService:
    def __init__(self, repo: MissionRepository, lifecycle: MissionLifecycleManager, bus: EventBus) -> None:
        self._repo = repo
        self._lifecycle = lifecycle
        self._bus = bus

    def create_mission(self, *, req: CreateMissionRequest, correlation_id: str) -> Mission:
        mission = Mission(mission_id=req.mission_id, field_id=req.field_id, status="draft")
        self._repo.create(mission)
        self._bus.publish("mission.created", {"mission_id": mission.mission_id}, correlation_id=correlation_id)
        return mission

    def schedule_mission(self, *, mission_id: str, scheduled_ts_ms: int, correlation_id: str) -> Mission:
        return self._lifecycle.transition(
            mission_id=mission_id,
            to_status="scheduled",
            scheduled_ts_ms=scheduled_ts_ms,
            correlation_id=correlation_id,
        )

    def assign_mission(self, *, mission_id: str, pilot_id: str, correlation_id: str) -> Mission:
        return self._lifecycle.transition(
            mission_id=mission_id,
            to_status="assigned",
            pilot_id=pilot_id,
            correlation_id=correlation_id,
        )


class DomainServicePort(Protocol):
    def execute(self, *, command: dict[str, Any], correlation_id: str) -> dict[str, Any]: ...


class AuditLogPort(Protocol):
    def append(self, *, event_type: str, correlation_id: str, payload: dict[str, Any]) -> None: ...


@dataclass(slots=True)
class MissionOrchestrationService:
    """Generic mission orchestration wrapper — delegates to a DomainServicePort.

    MissionService'den ayrı tutulur; bu sınıf use-case'i domain service portuna
    iletir ve audit log kaydı düşer (KR-081).
    """

    domain_service: DomainServicePort
    audit_log: AuditLogPort

    def orchestrate(self, *, command: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        # KR-081: contract doğrulaması üst akışta tamamlanmış payload üzerinden çalışılır.
        result = self.domain_service.execute(command=command, correlation_id=correlation_id)
        self.audit_log.append(
            event_type="MissionOrchestrationService.orchestrate",
            correlation_id=correlation_id,
            payload={"status": result.get("status", "ok")},
        )
        return result
