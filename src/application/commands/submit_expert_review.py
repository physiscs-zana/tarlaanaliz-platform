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
class SubmitExpertReviewCommand:
    review_id: str
    analysis_job_payload: dict[str, Any]
    verdict: str


@dataclass(frozen=True, slots=True)
class SubmitExpertReviewResult:
    review_id: str
    status: str
    correlation_id: str


class ExpertReviewServicePort(Protocol):
    def submit_review(
        self,
        *,
        review_id: str,
        reviewer_id: str,
        verdict: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> dict[str, Any]: ...


class ContractValidatorPort(Protocol):
    def validate(self, *, schema_key: str, payload: dict[str, Any]) -> None: ...


class CalibrationGatePort(Protocol):
    def ensure_calibrated(self, *, payload: dict[str, Any]) -> None: ...


class AuditLogPort(Protocol):
    def log(self, *, action: str, correlation_id: str, actor_id: str, payload: dict[str, Any]) -> None: ...


class SubmitExpertReviewDeps(Protocol):
    expert_review_service: ExpertReviewServicePort
    contract_validator: ContractValidatorPort
    calibration_gate: CalibrationGatePort
    audit_log: AuditLogPort


def handle(
    command: SubmitExpertReviewCommand, *, ctx: RequestContext, deps: SubmitExpertReviewDeps
) -> SubmitExpertReviewResult:
    if not {"expert", "admin"}.intersection(ctx.roles):
        raise PermissionError("forbidden")

    # KR-081: AnalysisJob payload contract-first şema ile doğrulanır.
    deps.contract_validator.validate(schema_key="analysis_job", payload=command.analysis_job_payload)

    # KR-018: kalibrasyon kanıtı olmadan review finalize edilmez.
    deps.calibration_gate.ensure_calibrated(payload=command.analysis_job_payload)

    submitted = deps.expert_review_service.submit_review(
        review_id=command.review_id,
        reviewer_id=ctx.actor_id,
        verdict=command.verdict,
        payload=command.analysis_job_payload,
        correlation_id=ctx.correlation_id,
    )

    deps.audit_log.log(
        action="submit_expert_review",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        payload={"review_id": command.review_id, "verdict": command.verdict, "error_code": None},
    )

    return SubmitExpertReviewResult(
        review_id=command.review_id,
        status=str(submitted.get("status", "submitted")),
        correlation_id=ctx.correlation_id,
    )
