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
class UpdatePilotCapacityCommand:
    pilot_id: str
    work_days: int
    daily_capacity: int
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class UpdatePilotCapacityResult:
    pilot_id: str
    work_days: int
    daily_capacity: int
    correlation_id: str


class PlanningCapacityPort(Protocol):
    def validate_capacity_update(self, *, pilot_id: str, work_days: int, daily_capacity: int) -> None: ...

    def update_capacity(self, *, pilot_id: str, work_days: int, daily_capacity: int) -> dict[str, Any]: ...


class AuditLogPort(Protocol):
    def log(self, *, action: str, correlation_id: str, actor_id: str, payload: dict[str, Any]) -> None: ...


class IdempotencyPort(Protocol):
    def get(self, *, key: str) -> dict[str, Any] | None: ...

    def set(self, *, key: str, value: dict[str, Any]) -> None: ...


class UpdatePilotCapacityDeps(Protocol):
    planning_capacity: PlanningCapacityPort
    audit_log: AuditLogPort
    idempotency: IdempotencyPort | None


def handle(
    command: UpdatePilotCapacityCommand,
    *,
    ctx: RequestContext,
    deps: UpdatePilotCapacityDeps,
) -> UpdatePilotCapacityResult:
    if not {"admin", "ops", "dispatcher"}.intersection(ctx.roles):
        raise PermissionError("forbidden")

    # KR-015: work_days <= 6 hard limit.
    if command.work_days > 6:
        raise ValueError("invalid_work_days")

    if command.idempotency_key and deps.idempotency is not None:
        cached = deps.idempotency.get(key=command.idempotency_key)
        if cached is not None:
            return UpdatePilotCapacityResult(
                pilot_id=str(cached["pilot_id"]),
                work_days=int(cached["work_days"]),
                daily_capacity=int(cached["daily_capacity"]),
                correlation_id=ctx.correlation_id,
            )

    deps.planning_capacity.validate_capacity_update(
        pilot_id=command.pilot_id,
        work_days=command.work_days,
        daily_capacity=command.daily_capacity,
    )
    updated = deps.planning_capacity.update_capacity(
        pilot_id=command.pilot_id,
        work_days=command.work_days,
        daily_capacity=command.daily_capacity,
    )

    deps.audit_log.log(
        action="update_pilot_capacity",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        payload={"pilot_id": command.pilot_id, "work_days": command.work_days, "error_code": None},
    )

    if command.idempotency_key and deps.idempotency is not None:
        deps.idempotency.set(
            key=command.idempotency_key,
            value={
                "pilot_id": command.pilot_id,
                "work_days": command.work_days,
                "daily_capacity": command.daily_capacity,
            },
        )

    return UpdatePilotCapacityResult(
        pilot_id=command.pilot_id,
        work_days=int(updated.get("work_days", command.work_days)),
        daily_capacity=int(updated.get("daily_capacity", command.daily_capacity)),
        correlation_id=ctx.correlation_id,
    )
