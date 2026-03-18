# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-063: Admin user listing — all users with roles and field info.
"""Admin user management endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

LOGGER = logging.getLogger("api.admin_users")

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminUserResponse(BaseModel):
    user_id: str
    phone: str
    display_name: str
    role: str
    province: str
    district: str
    active: bool


def _require_admin(request: Request) -> None:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if "admin" not in roles and "CENTRAL_ADMIN" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(request: Request) -> list[AdminUserResponse]:
    """List all users with their primary role (admin only)."""
    _require_admin(request)
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    async with get_async_session() as session:
        result = await session.execute(select(UserModel).options(selectinload(UserModel.roles)))
        models = result.scalars().unique().all()

    return [
        AdminUserResponse(
            user_id=str(m.user_id),
            phone=m.phone,
            display_name=m.display_name or f"{m.first_name} {m.last_name}".strip() or "",
            role=m.roles[0].role if m.roles else "—",
            province=m.province or "",
            district=m.district or "",
            active=m.is_active,
        )
        for m in models
    ]
