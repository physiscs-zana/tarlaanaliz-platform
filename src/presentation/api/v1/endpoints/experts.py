# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-063: Expert management endpoints — EXPERT role from canonical RBAC matrix.
"""Expert management endpoints — real DB CRUD against users with EXPERT role."""

from __future__ import annotations

import logging
import uuid as _uuid
from datetime import datetime, timezone

import bcrypt
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.core.domain.entities.user import User, UserRole
from src.infrastructure.persistence.sqlalchemy.models.expert_model import ExpertModel
from src.infrastructure.persistence.sqlalchemy.models.expert_review_model import ExpertReviewModel
from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
from src.infrastructure.persistence.sqlalchemy.models.user_role_model import UserRoleModel
from src.infrastructure.persistence.sqlalchemy.repositories.user_repository_impl import UserRepositoryImpl
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

LOGGER = logging.getLogger("api.experts")

router = APIRouter(prefix="/experts", tags=["experts"])


class ExpertCreateRequest(BaseModel):
    """Request body for creating a new expert user."""

    phone: str = Field(min_length=10, max_length=20)
    pin: str = Field(min_length=6, max_length=6, description="6-digit PIN (KR-050)")
    display_name: str = Field(min_length=2, max_length=80)
    province: str = Field(min_length=2, max_length=100)
    expertise_tags: list[str] = Field(default_factory=list, max_length=20)


class ExpertResponse(BaseModel):
    """Expert user data returned to admin."""

    user_id: str
    phone: str
    display_name: str
    province: str
    role: str
    expertise_tags: list[str] = []
    active: bool = True
    review_count: int = 0
    sla_rate: str = "\u2014"


def _require_admin(request: Request) -> None:
    """Raise 401/403 if caller is not admin."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if "admin" not in roles and "CENTRAL_ADMIN" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("", response_model=list[ExpertResponse])
async def list_experts(request: Request) -> list[ExpertResponse]:
    """List all experts with review counts and SLA rates (admin only)."""
    _require_admin(request)

    async with get_async_session() as session:
        # 1. Get all EXPERT role users
        user_result = await session.execute(
            select(UserModel)
            .join(UserRoleModel, UserModel.user_id == UserRoleModel.user_id)
            .where(UserRoleModel.role == UserRole.EXPERT.value)
        )
        models = user_result.scalars().unique().all()
        user_ids = [m.user_id for m in models]

        if not user_ids:
            return []

        # 2. Batch query: completed review count per expert (via experts table)
        review_counts: dict[_uuid.UUID, int] = {}
        sla_compliance: dict[_uuid.UUID, str] = {}

        # Map user_id → expert_id
        expert_result = await session.execute(
            select(ExpertModel.expert_id, ExpertModel.user_id).where(ExpertModel.user_id.in_(user_ids))
        )
        expert_rows = expert_result.all()
        user_to_expert: dict[_uuid.UUID, _uuid.UUID] = {row.user_id: row.expert_id for row in expert_rows}
        expert_ids = list(user_to_expert.values())

        if expert_ids:
            # Completed review counts per expert
            count_result = await session.execute(
                select(ExpertReviewModel.expert_id, func.count())
                .where(ExpertReviewModel.expert_id.in_(expert_ids))
                .where(ExpertReviewModel.status == "COMPLETED")
                .group_by(ExpertReviewModel.expert_id)
            )
            for row in count_result.all():
                review_counts[row[0]] = row[1]

            # SLA compliance: % of reviews completed within 4 hours of assignment
            for eid in expert_ids:
                total_result = await session.execute(
                    select(func.count())
                    .select_from(ExpertReviewModel)
                    .where(ExpertReviewModel.expert_id == eid)
                    .where(ExpertReviewModel.status.in_(["COMPLETED", "REJECTED"]))
                )
                total = total_result.scalar() or 0

                if total == 0:
                    continue

                on_time_result = await session.execute(
                    select(func.count())
                    .select_from(ExpertReviewModel)
                    .where(ExpertReviewModel.expert_id == eid)
                    .where(ExpertReviewModel.status.in_(["COMPLETED", "REJECTED"]))
                    .where(ExpertReviewModel.completed_at.isnot(None))
                    .where(ExpertReviewModel.assigned_at.isnot(None))
                    .where(
                        func.extract("epoch", ExpertReviewModel.completed_at)
                        - func.extract("epoch", ExpertReviewModel.assigned_at)
                        <= 4 * 3600  # 4 hours in seconds
                    )
                )
                on_time = on_time_result.scalar() or 0
                rate = round(on_time / total * 100)
                sla_compliance[eid] = f"%{rate}"

    return [
        ExpertResponse(
            user_id=str(m.user_id),
            phone=m.phone,
            display_name=m.display_name or f"{m.first_name} {m.last_name}".strip() or "",
            province=m.province or "",
            role=UserRole.EXPERT.value,
            expertise_tags=m.expertise_tags or [],
            active=m.is_active,
            review_count=review_counts.get(user_to_expert.get(m.user_id, _uuid.UUID(int=0)), 0),
            sla_rate=sla_compliance.get(user_to_expert.get(m.user_id, _uuid.UUID(int=0)), "\u2014"),
        )
        for m in models
    ]


@router.post("", response_model=ExpertResponse, status_code=status.HTTP_201_CREATED)
async def create_expert(request: Request, payload: ExpertCreateRequest) -> ExpertResponse:
    """Create a new expert user (admin only)."""
    _require_admin(request)

    async with get_async_session() as session:
        repo = UserRepositoryImpl(session)

        existing = await repo.find_by_phone_number(payload.phone)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already registered")

        now = datetime.now(timezone.utc)
        user = User(
            user_id=_uuid.uuid4(),
            phone_number=payload.phone,
            pin_hash=bcrypt.hashpw(payload.pin.encode(), bcrypt.gensalt()).decode(),
            role=UserRole.EXPERT,
            province=payload.province,
            created_at=now,
            updated_at=now,
        )
        await repo.save(user)

        # Save display_name and expertise_tags to user model
        result = await session.execute(select(UserModel).where(UserModel.user_id == user.user_id))
        user_model = result.scalar_one_or_none()
        if user_model:
            user_model.display_name = payload.display_name
            user_model.expertise_tags = payload.expertise_tags
        await session.commit()

    LOGGER.info("EXPERT.CREATED user_id=%s", user.user_id)
    return ExpertResponse(
        user_id=str(user.user_id),
        phone=payload.phone,
        display_name=payload.display_name,
        province=payload.province,
        role=UserRole.EXPERT.value,
        expertise_tags=payload.expertise_tags,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expert(request: Request, user_id: str) -> None:
    """Delete an expert user (admin only)."""
    _require_admin(request)
    from sqlalchemy import delete as sa_delete

    try:
        uid = _uuid.UUID(user_id)
    except ValueError as err:
        raise HTTPException(status_code=422, detail="Invalid user_id") from err

    async with get_async_session() as session:
        result = await session.execute(select(UserModel).where(UserModel.user_id == uid))
        user_model = result.scalar_one_or_none()
        if user_model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expert not found")

        await session.execute(sa_delete(UserRoleModel).where(UserRoleModel.user_id == uid))
        await session.delete(user_model)
        await session.commit()

    LOGGER.info("EXPERT.DELETED user_id=%s", user_id)
