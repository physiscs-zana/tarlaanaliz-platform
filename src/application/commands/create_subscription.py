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
class CreateSubscriptionCommand:
    field_id: str
    plan_id: str
    requested_status: str = "pending"
    payment_intent_id: str | None = None


@dataclass(frozen=True, slots=True)
class CreateSubscriptionResult:
    subscription_id: str
    status: str
    correlation_id: str


class SubscriptionServicePort(Protocol):
    def create_subscription(
        self, *, field_id: str, plan_id: str, status: str, correlation_id: str
    ) -> dict[str, Any]: ...


class PaymentServicePort(Protocol):
    def get_payment_intent(self, *, payment_intent_id: str) -> dict[str, Any] | None: ...


class AuditLogPort(Protocol):
    def log(self, *, action: str, correlation_id: str, actor_id: str, payload: dict[str, Any]) -> None: ...


class CreateSubscriptionDeps(Protocol):
    subscription_service: SubscriptionServicePort
    payment_service: PaymentServicePort | None
    audit_log: AuditLogPort


def handle(
    command: CreateSubscriptionCommand, *, ctx: RequestContext, deps: CreateSubscriptionDeps
) -> CreateSubscriptionResult:
    if not {"admin", "ops", "farmer"}.intersection(ctx.roles):
        raise PermissionError("forbidden")

    target_status = command.requested_status.lower()

    # KR-033: paid statüsüne geçişte PaymentIntent zorunludur.
    if target_status == "paid":
        if not command.payment_intent_id or deps.payment_service is None:
            raise ValueError("payment_intent_required")
        intent = deps.payment_service.get_payment_intent(payment_intent_id=command.payment_intent_id)
        if intent is None:
            raise ValueError("payment_intent_not_found")

    created = deps.subscription_service.create_subscription(
        field_id=command.field_id,
        plan_id=command.plan_id,
        status=target_status,
        correlation_id=ctx.correlation_id,
    )

    subscription_id = str(created.get("subscription_id", ""))
    if not subscription_id:
        raise RuntimeError("subscription_create_failed")

    deps.audit_log.log(
        action="create_subscription",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        payload={
            "subscription_id": subscription_id,
            "field_id": command.field_id,
            "status": target_status,
            "error_code": None,
        },
    )

    return CreateSubscriptionResult(
        subscription_id=subscription_id,
        status=target_status,
        correlation_id=ctx.correlation_id,
    )
