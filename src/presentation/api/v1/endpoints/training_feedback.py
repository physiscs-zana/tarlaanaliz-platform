# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-017: Training feedback endpoints.
"""Training feedback endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/training-feedback", tags=["training-feedback"])


class TrainingFeedbackCreateRequest(BaseModel):
    analysis_job_id: str = Field(min_length=3, max_length=64)
    score: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=500)


class TrainingFeedbackResponse(BaseModel):
    feedback_id: str
    analysis_job_id: str
    score: int
    created_at: datetime


class TrainingFeedbackService(Protocol):
    def create(self, payload: TrainingFeedbackCreateRequest, actor_subject: str) -> TrainingFeedbackResponse: ...


@dataclass(slots=True)
class _InMemoryTrainingFeedbackService:
    def create(self, payload: TrainingFeedbackCreateRequest, actor_subject: str) -> TrainingFeedbackResponse:
        _ = actor_subject
        return TrainingFeedbackResponse(
            feedback_id="tfb-1",
            analysis_job_id=payload.analysis_job_id,
            score=payload.score,
            created_at=datetime.utcnow(),
        )


def get_training_feedback_service(request: Request) -> TrainingFeedbackService:
    services = getattr(request.app.state, "services", None)
    if services is not None:
        svc = services.get("training_feedback_service")
        if svc is not None:
            return cast(TrainingFeedbackService, svc)
    return _InMemoryTrainingFeedbackService()


def _require_subject(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return str(getattr(user, "subject", ""))


@router.post("", response_model=TrainingFeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_training_feedback(
    request: Request,
    payload: TrainingFeedbackCreateRequest,
    service: TrainingFeedbackService = Depends(get_training_feedback_service),
) -> TrainingFeedbackResponse:
    subject = _require_subject(request)
    return service.create(payload=payload, actor_subject=subject)
