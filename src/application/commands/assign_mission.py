# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: Command contracts are defined before orchestration logic.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class RequestContext:
    actor_id: str
    roles: tuple[str, ...]
    correlation_id: str


@dataclass(frozen=True, slots=True)
class AssignMissionCommand:
    mission_id: str
    pilot_id: str
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class AssignMissionResult:
    mission_id: str
    pilot_id: str
    status: str
    correlation_id: str


class MissionServicePort(Protocol):
    def assign_mission(self, *, mission_id: str, pilot_id: str, correlation_id: str) -> dict[str, Any]: ...


class PlanningCapacityPort(Protocol):
    def ensure_assignment_allowed(self, *, pilot_id: str, mission_id: str) -> None: ...


class AuditLogPort(Protocol):
    def log(self, *, action: str, correlation_id: str, actor_id: str, payload: dict[str, Any]) -> None: ...


class IdempotencyPort(Protocol):
    def get(self, *, key: str) -> dict[str, Any] | None: ...

    def set(self, *, key: str, value: dict[str, Any]) -> None: ...


class AssignMissionDeps(Protocol):
    mission_service: MissionServicePort
    planning_capacity: PlanningCapacityPort
    audit_log: AuditLogPort
    idempotency: IdempotencyPort | None


def _require_role(ctx: RequestContext) -> None:
    if not {"admin", "ops", "dispatcher"}.intersection(ctx.roles):
        raise PermissionError("forbidden")


def handle(command: AssignMissionCommand, *, ctx: RequestContext, deps: AssignMissionDeps) -> AssignMissionResult:
    _require_role(ctx)

    if command.idempotency_key and deps.idempotency is not None:
        cached = deps.idempotency.get(key=command.idempotency_key)
        if cached is not None:
            return AssignMissionResult(
                mission_id=str(cached["mission_id"]),
                pilot_id=str(cached["pilot_id"]),
                status=str(cached["status"]),
                correlation_id=ctx.correlation_id,
            )

    # KR-015: atama öncesi kapasite/planning uygunluğu servis üzerinden doğrulanır.
    deps.planning_capacity.ensure_assignment_allowed(pilot_id=command.pilot_id, mission_id=command.mission_id)

    assigned = deps.mission_service.assign_mission(
        mission_id=command.mission_id,
        pilot_id=command.pilot_id,
        correlation_id=ctx.correlation_id,
    )

    deps.audit_log.log(
        action="assign_mission",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        payload={"mission_id": command.mission_id, "pilot_id": command.pilot_id, "error_code": None},
    )

    if command.idempotency_key and deps.idempotency is not None:
        deps.idempotency.set(
            key=command.idempotency_key,
            value={
                "mission_id": command.mission_id,
                "pilot_id": command.pilot_id,
                "status": assigned.get("status", "assigned"),
            },
        )

    return AssignMissionResult(
        mission_id=command.mission_id,
        pilot_id=command.pilot_id,
        status=str(assigned.get("status", "assigned")),
        correlation_id=ctx.correlation_id,
    )
