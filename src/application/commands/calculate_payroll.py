# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: Command contracts are defined before orchestration logic.

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RequestContext:
    actor_id: str
    roles: tuple[str, ...]
    correlation_id: str


@dataclass(frozen=True, slots=True)
class CalculatePayrollCommand:
    period_start: str
    period_end: str
    actor_type: str


@dataclass(frozen=True, slots=True)
class CalculatePayrollResult:
    actor_type: str
    gross_total: Decimal
    item_count: int
    correlation_id: str


class PayrollServicePort(Protocol):
    def calculate_payroll(self, *, period_start: str, period_end: str, actor_type: str) -> dict[str, object]: ...


class AuditLogPort(Protocol):
    def log(self, *, action: str, correlation_id: str, actor_id: str, payload: dict[str, object]) -> None: ...


class CalculatePayrollDeps(Protocol):
    payroll_service: PayrollServicePort
    audit_log: AuditLogPort


def handle(
    command: CalculatePayrollCommand, *, ctx: RequestContext, deps: CalculatePayrollDeps
) -> CalculatePayrollResult:
    if not {"admin", "finance"}.intersection(ctx.roles):
        raise PermissionError("forbidden")

    if command.actor_type not in {"pilot", "expert"}:
        raise ValueError("invalid_actor_type")

    calculated = deps.payroll_service.calculate_payroll(
        period_start=command.period_start,
        period_end=command.period_end,
        actor_type=command.actor_type,
    )

    deps.audit_log.log(
        action="calculate_payroll",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        payload={
            "period_start": command.period_start,
            "period_end": command.period_end,
            "actor_type": command.actor_type,
            "error_code": None,
        },
    )

    return CalculatePayrollResult(
        actor_type=command.actor_type,
        gross_total=Decimal(str(calculated.get("gross_total", "0"))),
        item_count=int(str(calculated.get("item_count", 0))),
        correlation_id=ctx.correlation_id,
    )
