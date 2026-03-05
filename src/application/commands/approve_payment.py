# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: Command contracts are defined before orchestration logic.

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class RequestContext:
    actor_id: str
    roles: tuple[str, ...]
    correlation_id: str
    request_id: str | None = None


@dataclass(frozen=True, slots=True)
class ApprovePaymentCommand:
    payment_intent_id: str
    payment_ref: str
    receipt_ref: str
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class ApprovePaymentResult:
    payment_intent_id: str
    status: str
    approved_by: str
    correlation_id: str


class PaymentServicePort(Protocol):
    def get_payment_intent(self, *, payment_intent_id: str) -> dict[str, Any] | None: ...

    def approve_payment(
        self,
        *,
        payment_intent_id: str,
        payment_ref: str,
        receipt_ref: str,
        approved_by: str,
        correlation_id: str,
    ) -> dict[str, Any]: ...


class AuditLogPort(Protocol):
    def log(self, *, action: str, correlation_id: str, actor_id: str, payload: dict[str, Any]) -> None: ...


class IdempotencyPort(Protocol):
    def get(self, *, key: str) -> dict[str, Any] | None: ...

    def set(self, *, key: str, value: dict[str, Any]) -> None: ...


class ApprovePaymentDeps(Protocol):
    payment_service: PaymentServicePort
    audit_log: AuditLogPort
    idempotency: IdempotencyPort | None


def _require_any_role(ctx: RequestContext, allowed: set[str]) -> None:
    if not allowed.intersection(ctx.roles):
        raise PermissionError("forbidden")


def handle(command: ApprovePaymentCommand, *, ctx: RequestContext, deps: ApprovePaymentDeps) -> ApprovePaymentResult:
    started_at = perf_counter()
    _require_any_role(ctx, {"admin", "ops", "finance"})

    if command.idempotency_key and deps.idempotency is not None:
        cached = deps.idempotency.get(key=command.idempotency_key)
        if cached is not None:
            return ApprovePaymentResult(
                payment_intent_id=str(cached["payment_intent_id"]),
                status=str(cached["status"]),
                approved_by=str(cached["approved_by"]),
                correlation_id=ctx.correlation_id,
            )

    # KR-033: PaymentIntent olmadan paid transition yok.
    intent = deps.payment_service.get_payment_intent(payment_intent_id=command.payment_intent_id)
    if intent is None:
        raise ValueError("payment_intent_not_found")

    if str(intent.get("status", "")).lower() == "paid":
        return ApprovePaymentResult(
            payment_intent_id=command.payment_intent_id,
            status="paid",
            approved_by=str(intent.get("approved_by", ctx.actor_id)),
            correlation_id=ctx.correlation_id,
        )

    approved = deps.payment_service.approve_payment(
        payment_intent_id=command.payment_intent_id,
        payment_ref=command.payment_ref,
        receipt_ref=command.receipt_ref,
        approved_by=ctx.actor_id,
        correlation_id=ctx.correlation_id,
    )

    deps.audit_log.log(
        action="approve_payment",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        payload={
            "payment_intent_id": command.payment_intent_id,
            "payment_ref": command.payment_ref,
            "latency_ms": int((perf_counter() - started_at) * 1000),
            "error_code": None,
        },
    )

    if command.idempotency_key and deps.idempotency is not None:
        deps.idempotency.set(
            key=command.idempotency_key,
            value={
                "payment_intent_id": command.payment_intent_id,
                "status": str(approved.get("status", "paid")),
                "approved_by": ctx.actor_id,
            },
        )

    return ApprovePaymentResult(
        payment_intent_id=command.payment_intent_id,
        status=str(approved.get("status", "paid")),
        approved_by=ctx.actor_id,
        correlation_id=ctx.correlation_id,
    )
