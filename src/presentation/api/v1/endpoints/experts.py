# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-063: Expert management endpoints — EXPERT role from canonical RBAC matrix.
"""Expert management endpoints — real DB CRUD against users with EXPERT role."""

from __future__ import annotations

import hashlib
import logging
import uuid as _uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.core.domain.entities.user import User, UserRole
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
    async with get_async_session() as session:
        repo = UserRepositoryImpl(session)
        experts = await repo.list_by_role(UserRole.EXPERT)
    return [
        ExpertResponse(
            user_id=str(e.user_id),
            phone=e.phone_number,
            display_name="",
            province=e.province,
            role=e.role.value,
        )
        for e in experts
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
            pin_hash=hashlib.sha256(payload.pin.encode()).hexdigest(),
            role=UserRole.EXPERT,
            province=payload.province,
            created_at=now,
            updated_at=now,
        )
        await repo.save(user)
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
