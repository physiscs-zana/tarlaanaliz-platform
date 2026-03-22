# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-063: Expert portal review endpoints.
# KR-019: Ownership check — uzman yalnizca kendisine atanmis incelemeleri gorur.
# KR-029: Training feedback — verdict + training_grade.
"""Expert portal review queue, stats, SLA, and submit endpoints."""

from __future__ import annotations

import logging
import uuid as _uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from src.infrastructure.persistence.sqlalchemy.models.expert_model import ExpertModel
from src.infrastructure.persistence.sqlalchemy.models.expert_review_model import ExpertReviewModel
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

_LOGGER = logging.getLogger("api.expert_portal")

router = APIRouter(prefix="/expert-portal", tags=["expert-portal"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------
class ReviewQueueItem(BaseModel):
    """Single item in the expert review queue."""

    review_id: str
    mission_id: str
    analysis_result_id: str
    status: str
    assigned_at: str
    priority: int = 0


class ReviewSubmitRequest(BaseModel):
    """Expert submits a verdict for a review."""

    decision: str = Field(pattern=r"^(confirmed|corrected|rejected|needs_more_expert|approve|reject|needs_revision)$")
    notes: str | None = Field(default=None, max_length=500)
    training_grade: str | None = Field(default=None, pattern=r"^[A-D]$|^REJECT$")
    grade_reason: str | None = Field(default=None, max_length=200)


class ReviewSubmitResponse(BaseModel):
    """Response after submitting a review verdict."""

    review_id: str
    status: str
    submitted_at: datetime


class ExpertStatsResponse(BaseModel):
    """Expert's own performance stats."""

    total_completed: int
    pending_count: int
    in_progress_count: int
    completed_today: int
    avg_completion_minutes: float | None


class ExpertSlaResponse(BaseModel):
    """Expert SLA metrics."""

    avg_first_response_minutes: float | None
    open_sla_risk_count: int


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------
def _require_expert(request: Request) -> str:
    """Extract authenticated expert subject (user_id). Raises 401/403."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if not roles & {"expert", "EXPERT", "admin", "CENTRAL_ADMIN"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return str(getattr(user, "subject", ""))


async def _get_expert_id(subject: str) -> _uuid.UUID | None:
    """Resolve expert_id from user_id (subject) via experts table."""
    try:
        user_uuid = _uuid.UUID(subject)
    except ValueError:
        return None
    async with get_async_session() as session:
        result = await session.execute(select(ExpertModel.expert_id).where(ExpertModel.user_id == user_uuid))
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# GET /expert-portal/reviews/queue — pending reviews for this expert
# ---------------------------------------------------------------------------
@router.get("/reviews/queue", response_model=list[ReviewQueueItem])
async def get_review_queue(
    request: Request,
    limit: int = Query(default=25, ge=1, le=100),
) -> list[ReviewQueueItem]:
    """Return pending/in-progress reviews assigned to the authenticated expert."""
    subject = _require_expert(request)
    expert_id = await _get_expert_id(subject)
    if expert_id is None:
        return []

    async with get_async_session() as session:
        result = await session.execute(
            select(ExpertReviewModel)
            .where(ExpertReviewModel.expert_id == expert_id)
            .where(ExpertReviewModel.status.in_(["PENDING", "IN_PROGRESS"]))
            .order_by(ExpertReviewModel.assigned_at.asc())
            .limit(limit)
        )
        reviews = result.scalars().all()

    return [
        ReviewQueueItem(
            review_id=str(r.review_id),
            mission_id=str(r.mission_id),
            analysis_result_id=str(r.analysis_result_id),
            status=r.status,
            assigned_at=r.assigned_at.isoformat() if r.assigned_at else "",
            priority=0,
        )
        for r in reviews
    ]


# ---------------------------------------------------------------------------
# POST /expert-portal/reviews/{review_id}/submit — submit verdict
# ---------------------------------------------------------------------------
@router.post("/reviews/{review_id}/submit", response_model=ReviewSubmitResponse)
async def submit_review(
    request: Request,
    review_id: str,
    payload: ReviewSubmitRequest,
) -> ReviewSubmitResponse:
    """Submit expert verdict for a review (KR-019 ownership check enforced)."""
    subject = _require_expert(request)
    expert_id = await _get_expert_id(subject)
    if expert_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Expert profile not found")

    try:
        review_uuid = _uuid.UUID(review_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid review_id") from None

    now = datetime.now(timezone.utc)

    async with get_async_session() as session:
        result = await session.execute(select(ExpertReviewModel).where(ExpertReviewModel.review_id == review_uuid))
        review = result.scalar_one_or_none()
        if review is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

        # KR-019: Ownership check — expert can only submit their own reviews
        if review.expert_id != expert_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu inceleme size atanmamis.")

        if review.status == "COMPLETED":
            return ReviewSubmitResponse(
                review_id=review_id, status="COMPLETED", submitted_at=review.completed_at or now
            )

        # Transition: PENDING → start + complete; IN_PROGRESS → complete
        if review.started_at is None:
            review.started_at = now

        # Map legacy decision values
        decision = payload.decision
        if decision == "approve":
            decision = "confirmed"
        elif decision == "reject":
            decision = "rejected"
        elif decision == "needs_revision":
            decision = "needs_more_expert"

        review.status = "REJECTED" if decision == "rejected" else "COMPLETED"
        review.completed_at = now
        review.verdict = decision
        review.training_grade = payload.training_grade
        review.grade_reason = payload.grade_reason
        await session.commit()

    _LOGGER.warning(
        "EXPERT_REVIEW.SUBMITTED review=%s expert=%s verdict=%s grade=%s",
        review_id,
        expert_id,
        decision,
        payload.training_grade,
    )

    # KR-029: Training feedback event — verdict + grade eğitim hattına gönderilir
    if payload.training_grade:
        _LOGGER.warning(
            "TRAINING.FEEDBACK_RECORDED review=%s grade=%s mission=%s",
            review_id,
            payload.training_grade,
            str(review.mission_id) if review else "unknown",
        )

    return ReviewSubmitResponse(review_id=review_id, status=review.status, submitted_at=now)


# ---------------------------------------------------------------------------
# GET /expert-portal/my-stats — expert's own performance stats
# ---------------------------------------------------------------------------
@router.get("/my-stats", response_model=ExpertStatsResponse)
async def get_my_stats(request: Request) -> ExpertStatsResponse:
    """Return authenticated expert's review performance stats."""
    subject = _require_expert(request)
    expert_id = await _get_expert_id(subject)
    if expert_id is None:
        return ExpertStatsResponse(
            total_completed=0,
            pending_count=0,
            in_progress_count=0,
            completed_today=0,
            avg_completion_minutes=None,
        )

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    async with get_async_session() as session:
        base = select(ExpertReviewModel).where(ExpertReviewModel.expert_id == expert_id)

        total_completed = (
            await session.execute(
                select(func.count()).select_from(base.where(ExpertReviewModel.status == "COMPLETED").subquery())
            )
        ).scalar() or 0

        pending_count = (
            await session.execute(
                select(func.count()).select_from(base.where(ExpertReviewModel.status == "PENDING").subquery())
            )
        ).scalar() or 0

        in_progress_count = (
            await session.execute(
                select(func.count()).select_from(base.where(ExpertReviewModel.status == "IN_PROGRESS").subquery())
            )
        ).scalar() or 0

        completed_today = (
            await session.execute(
                select(func.count()).select_from(
                    base.where(ExpertReviewModel.status == "COMPLETED")
                    .where(ExpertReviewModel.completed_at >= today_start)
                    .subquery()
                )
            )
        ).scalar() or 0

        # Average completion time in minutes (started_at → completed_at)
        avg_seconds = (
            await session.execute(
                select(
                    func.avg(
                        func.extract("epoch", ExpertReviewModel.completed_at)
                        - func.extract("epoch", ExpertReviewModel.started_at)
                    )
                )
                .where(ExpertReviewModel.expert_id == expert_id)
                .where(ExpertReviewModel.status == "COMPLETED")
                .where(ExpertReviewModel.started_at.isnot(None))
                .where(ExpertReviewModel.completed_at.isnot(None))
            )
        ).scalar()

    avg_minutes = round(avg_seconds / 60, 1) if avg_seconds else None

    return ExpertStatsResponse(
        total_completed=total_completed,
        pending_count=pending_count,
        in_progress_count=in_progress_count,
        completed_today=completed_today,
        avg_completion_minutes=avg_minutes,
    )


# ---------------------------------------------------------------------------
# GET /expert-portal/sla — SLA metrics for this expert
# ---------------------------------------------------------------------------
@router.get("/sla", response_model=ExpertSlaResponse)
async def get_sla(request: Request) -> ExpertSlaResponse:
    """Return SLA metrics for the authenticated expert."""
    subject = _require_expert(request)
    expert_id = await _get_expert_id(subject)
    if expert_id is None:
        return ExpertSlaResponse(avg_first_response_minutes=None, open_sla_risk_count=0)

    async with get_async_session() as session:
        # Average first response = assigned_at → started_at (in minutes)
        avg_seconds = (
            await session.execute(
                select(
                    func.avg(
                        func.extract("epoch", ExpertReviewModel.started_at)
                        - func.extract("epoch", ExpertReviewModel.assigned_at)
                    )
                )
                .where(ExpertReviewModel.expert_id == expert_id)
                .where(ExpertReviewModel.started_at.isnot(None))
            )
        ).scalar()

        # Open SLA risk: PENDING reviews older than 3 hours (of 4-hour SLA)
        from datetime import timedelta

        sla_warning_threshold = datetime.now(timezone.utc) - timedelta(hours=3)
        risk_count = (
            await session.execute(
                select(func.count())
                .select_from(ExpertReviewModel)
                .where(ExpertReviewModel.expert_id == expert_id)
                .where(ExpertReviewModel.status.in_(["PENDING", "IN_PROGRESS"]))
                .where(ExpertReviewModel.assigned_at <= sla_warning_threshold)
            )
        ).scalar() or 0

    avg_minutes = round(avg_seconds / 60, 1) if avg_seconds else None
    return ExpertSlaResponse(avg_first_response_minutes=avg_minutes, open_sla_risk_count=risk_count)


# ---------------------------------------------------------------------------
# GET /expert-portal/me/expertise — expert's competency tags
# ---------------------------------------------------------------------------
@router.get("/me/expertise")
async def get_my_expertise(request: Request) -> dict[str, list[str]]:
    """Return current expert's expertise_tags from database."""
    subject = _require_expert(request)
    from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel

    try:
        user_uuid = _uuid.UUID(subject)
    except ValueError:
        return {"expertise_tags": []}

    async with get_async_session() as session:
        result = await session.execute(select(UserModel.expertise_tags).where(UserModel.user_id == user_uuid))
        tags = result.scalar_one_or_none()

    return {"expertise_tags": tags or []}
