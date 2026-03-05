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
class SubmitTrainingFeedbackCommand:
    feedback_id: str
    review_id: str
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SubmitTrainingFeedbackResult:
    feedback_id: str
    status: str
    correlation_id: str


class TrainingFeedbackServicePort(Protocol):
    def submit_feedback(
        self,
        *,
        feedback_id: str,
        review_id: str,
        actor_id: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> dict[str, Any]: ...


class ContractValidatorPort(Protocol):
    def validate(self, *, schema_key: str, payload: dict[str, Any]) -> None: ...


class AuditLogPort(Protocol):
    def log(self, *, action: str, correlation_id: str, actor_id: str, payload: dict[str, Any]) -> None: ...


class SubmitTrainingFeedbackDeps(Protocol):
    training_feedback_service: TrainingFeedbackServicePort
    contract_validator: ContractValidatorPort
    audit_log: AuditLogPort


def handle(
    command: SubmitTrainingFeedbackCommand,
    *,
    ctx: RequestContext,
    deps: SubmitTrainingFeedbackDeps,
) -> SubmitTrainingFeedbackResult:
    if not {"expert", "admin", "ops"}.intersection(ctx.roles):
        raise PermissionError("forbidden")

    # KR-081: feedback payload schema doğrulaması contract-first yapılır.
    deps.contract_validator.validate(schema_key="training_feedback", payload=command.payload)

    # KR-071: çıktı yalnızca outbound feedback kaydı üzerinden iletilir.
    submitted = deps.training_feedback_service.submit_feedback(
        feedback_id=command.feedback_id,
        review_id=command.review_id,
        actor_id=ctx.actor_id,
        payload=command.payload,
        correlation_id=ctx.correlation_id,
    )

    deps.audit_log.log(
        action="submit_training_feedback",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        payload={"feedback_id": command.feedback_id, "review_id": command.review_id, "error_code": None},
    )

    return SubmitTrainingFeedbackResult(
        feedback_id=command.feedback_id,
        status=str(submitted.get("status", "submitted")),
        correlation_id=ctx.correlation_id,
    )
