# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015: Pilot management endpoints.
# KR-063: PILOT role from canonical RBAC matrix.
"""Pilot management endpoints — real DB CRUD against users with PILOT role."""

from __future__ import annotations

import logging
import uuid as _uuid
from datetime import datetime, timezone

import bcrypt
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.core.domain.entities.user import User, UserRole
from src.infrastructure.persistence.sqlalchemy.repositories.user_repository_impl import UserRepositoryImpl
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

LOGGER = logging.getLogger("api.pilots")

router = APIRouter(prefix="/pilots", tags=["pilots"])


class PilotCreateRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    pin: str = Field(min_length=6, max_length=6, description="6-digit PIN (KR-050)")
    display_name: str = Field(min_length=2, max_length=80)
    province: str = Field(min_length=2, max_length=100)
    license_no: str = Field(default="", max_length=32)


class PilotResponse(BaseModel):
    user_id: str
    phone: str
    display_name: str
    province: str
    role: str
    active: bool = True


def _require_admin(request: Request) -> None:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if "admin" not in roles and "CENTRAL_ADMIN" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("", response_model=list[PilotResponse])
async def list_pilots(request: Request) -> list[PilotResponse]:
    """List all users with PILOT role (admin only)."""
    _require_admin(request)
    async with get_async_session() as session:
        repo = UserRepositoryImpl(session)
        pilots = await repo.list_by_role(UserRole.PILOT)
    return [
        PilotResponse(
            user_id=str(p.user_id),
            phone=p.phone_number,
            display_name="",  # UserModel doesn't store display_name separately
            province=p.province,
            role=p.role.value,
        )
        for p in pilots
    ]


@router.post("", response_model=PilotResponse, status_code=status.HTTP_201_CREATED)
async def create_pilot(request: Request, payload: PilotCreateRequest) -> PilotResponse:
    """Create a new pilot user (admin only)."""
    _require_admin(request)

    async with get_async_session() as session:
        repo = UserRepositoryImpl(session)

        # Check if phone already registered
        existing = await repo.find_by_phone_number(payload.phone)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already registered")

        now = datetime.now(timezone.utc)
        user = User(
            user_id=_uuid.uuid4(),
            phone_number=payload.phone,
            pin_hash=bcrypt.hashpw(payload.pin.encode(), bcrypt.gensalt()).decode(),
            role=UserRole.PILOT,
            province=payload.province,
            created_at=now,
            updated_at=now,
        )
        await repo.save(user)
        await session.commit()

    LOGGER.info("PILOT.CREATED user_id=%s phone=%s", user.user_id, payload.phone[-4:])
    return PilotResponse(
        user_id=str(user.user_id),
        phone=payload.phone,
        display_name=payload.display_name,
        province=payload.province,
        role=UserRole.PILOT.value,
    )
