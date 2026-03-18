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

from src.core.domain.entities.user import User, UserRole
from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
from src.infrastructure.persistence.sqlalchemy.repositories.user_repository_impl import UserRepositoryImpl
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

LOGGER = logging.getLogger("api.experts")

router = APIRouter(prefix="/experts", tags=["experts"])


class ExpertCreateRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    pin: str = Field(min_length=6, max_length=6, description="6-digit PIN (KR-050)")
    display_name: str = Field(min_length=2, max_length=80)
    province: str = Field(min_length=2, max_length=100)
    expertise_tags: list[str] = Field(default_factory=list, max_length=20)


class ExpertResponse(BaseModel):
    user_id: str
    phone: str
    display_name: str
    province: str
    role: str
    expertise_tags: list[str] = []
    active: bool = True


def _require_admin(request: Request) -> None:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if "admin" not in roles and "CENTRAL_ADMIN" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("", response_model=list[ExpertResponse])
async def list_experts(request: Request) -> list[ExpertResponse]:
    """List all users with EXPERT role (admin only)."""
    _require_admin(request)
    from sqlalchemy import select

    async with get_async_session() as session:
        from src.infrastructure.persistence.sqlalchemy.models.user_role_model import UserRoleModel

        result = await session.execute(
            select(UserModel)
            .join(UserRoleModel, UserModel.user_id == UserRoleModel.user_id)
            .where(UserRoleModel.role == UserRole.EXPERT.value)
        )
        models = result.scalars().unique().all()
    return [
        ExpertResponse(
            user_id=str(m.user_id),
            phone=m.phone,
            display_name=m.display_name or f"{m.first_name} {m.last_name}".strip() or "",
            province=m.province or "",
            role=UserRole.EXPERT.value,
            expertise_tags=m.expertise_tags or [],
            active=m.is_active,
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
        from sqlalchemy import select

        result = await session.execute(select(UserModel).where(UserModel.user_id == user.user_id))
        user_model = result.scalar_one_or_none()
        if user_model:
            user_model.display_name = payload.display_name
            user_model.expertise_tags = payload.expertise_tags
        await session.commit()

    LOGGER.info("EXPERT.CREATED user_id=%s phone=%s", user.user_id, payload.phone[-4:])
    return ExpertResponse(
        user_id=str(user.user_id),
        phone=payload.phone,
        display_name=payload.display_name,
        province=payload.province,
        role=UserRole.EXPERT.value,
        expertise_tags=payload.expertise_tags,
    )
