# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
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
class ScheduleMissionCommand:
    subscription_id: str
    scheduled_for: str
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class ScheduleMissionResult:
    mission_id: str
    scheduled_for: str
    status: str
    correlation_id: str


class MissionLifecyclePort(Protocol):
    def schedule_mission(self, *, subscription_id: str, scheduled_for: str, correlation_id: str) -> dict[str, Any]: ...


class PlanningCapacityPort(Protocol):
    def ensure_slot_available(self, *, subscription_id: str, scheduled_for: str) -> None: ...


class AuditLogPort(Protocol):
    def log(self, *, action: str, correlation_id: str, actor_id: str, payload: dict[str, Any]) -> None: ...


class IdempotencyPort(Protocol):
    def get(self, *, key: str) -> dict[str, Any] | None: ...

    def set(self, *, key: str, value: dict[str, Any]) -> None: ...


class ScheduleMissionDeps(Protocol):
    mission_lifecycle_manager: MissionLifecyclePort
    planning_capacity: PlanningCapacityPort
    audit_log: AuditLogPort
    idempotency: IdempotencyPort | None


def handle(command: ScheduleMissionCommand, *, ctx: RequestContext, deps: ScheduleMissionDeps) -> ScheduleMissionResult:
    if not {"admin", "ops", "dispatcher"}.intersection(ctx.roles):
        raise PermissionError("forbidden")

    if command.idempotency_key and deps.idempotency is not None:
        cached = deps.idempotency.get(key=command.idempotency_key)
        if cached is not None:
            return ScheduleMissionResult(
                mission_id=str(cached["mission_id"]),
                scheduled_for=str(cached["scheduled_for"]),
                status=str(cached["status"]),
                correlation_id=ctx.correlation_id,
            )

    # KR-015: zamanlama kapasite kontrolü planlama servisi üzerinden yapılır.
    deps.planning_capacity.ensure_slot_available(
        subscription_id=command.subscription_id,
        scheduled_for=command.scheduled_for,
    )

    scheduled = deps.mission_lifecycle_manager.schedule_mission(
        subscription_id=command.subscription_id,
        scheduled_for=command.scheduled_for,
        correlation_id=ctx.correlation_id,
    )

    mission_id = str(scheduled.get("mission_id", ""))
    if not mission_id:
        raise RuntimeError("mission_schedule_failed")

    deps.audit_log.log(
        action="schedule_mission",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        payload={"subscription_id": command.subscription_id, "mission_id": mission_id, "error_code": None},
    )

    if command.idempotency_key and deps.idempotency is not None:
        deps.idempotency.set(
            key=command.idempotency_key,
            value={"mission_id": mission_id, "scheduled_for": command.scheduled_for, "status": "scheduled"},
        )

    return ScheduleMissionResult(
        mission_id=mission_id,
        scheduled_for=command.scheduled_for,
        status=str(scheduled.get("status", "scheduled")),
        correlation_id=ctx.correlation_id,
    )
