# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-063: Expert portal review endpoints.
"""Expert portal review queue and submit endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/expert-portal", tags=["expert-portal"])


class ReviewQueueItem(BaseModel):
    review_id: str
    analysis_job_id: str
    priority: int


class ReviewSubmitRequest(BaseModel):
    decision: str = Field(pattern="^(approve|reject|needs_revision)$")
    notes: str | None = Field(default=None, max_length=500)


class ReviewSubmitResponse(BaseModel):
    review_id: str
    submitted_at: datetime


class ExpertPortalService(Protocol):
    def list_queue(self, expert_subject: str, limit: int) -> list[ReviewQueueItem]: ...

    def submit(self, review_id: str, payload: ReviewSubmitRequest, expert_subject: str) -> ReviewSubmitResponse: ...


@dataclass(slots=True)
class _InMemoryExpertPortalService:
    def list_queue(self, expert_subject: str, limit: int) -> list[ReviewQueueItem]:
        _ = expert_subject
        return [ReviewQueueItem(review_id="rvw-1", analysis_job_id="aj-1", priority=1)][:limit]

    def submit(self, review_id: str, payload: ReviewSubmitRequest, expert_subject: str) -> ReviewSubmitResponse:
        _ = payload, expert_subject
        return ReviewSubmitResponse(review_id=review_id, submitted_at=datetime.now(timezone.utc))


def get_expert_portal_service(request: Request) -> ExpertPortalService:
    services = getattr(request.app.state, "services", None)
    if services is not None:
        svc = services.get("expert_portal_service")
        if svc is not None:
            return cast(ExpertPortalService, svc)
    return _InMemoryExpertPortalService()


def _require_expert(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if not roles & {"expert", "EXPERT", "admin", "CENTRAL_ADMIN"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return str(getattr(user, "subject", ""))


@router.get("/reviews/queue", response_model=list[ReviewQueueItem])
def get_review_queue(
    request: Request,
    limit: int = Query(default=25, ge=1, le=100),
    service: ExpertPortalService = Depends(get_expert_portal_service),
) -> list[ReviewQueueItem]:
    # KR-081: review queue contract kept explicit at API boundary.
    subject = _require_expert(request)
    return service.list_queue(expert_subject=subject, limit=limit)


@router.post("/reviews/{review_id}/submit", response_model=ReviewSubmitResponse)
def submit_review(
    request: Request,
    review_id: str,
    payload: ReviewSubmitRequest,
    service: ExpertPortalService = Depends(get_expert_portal_service),
) -> ReviewSubmitResponse:
    subject = _require_expert(request)
    return service.submit(review_id=review_id, payload=payload, expert_subject=subject)


@router.get("/me/expertise")
async def get_my_expertise(request: Request) -> dict[str, list[str]]:
    """Return current expert's expertise_tags from database."""
    subject = _require_expert(request)
    from sqlalchemy import select
    from src.infrastructure.persistence.sqlalchemy.session import get_async_session
    from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
    import uuid as _uuid

    try:
        user_uuid = _uuid.UUID(subject)
    except ValueError:
        return {"expertise_tags": []}

    async with get_async_session() as session:
        result = await session.execute(select(UserModel.expertise_tags).where(UserModel.user_id == user_uuid))
        tags = result.scalar_one_or_none()

    return {"expertise_tags": tags or []}
