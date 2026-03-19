# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-063: Admin user listing — farmers with field/parcel info.
"""Admin user management endpoints."""

from __future__ import annotations

import logging
import uuid as _uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.orm import selectinload

from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel
from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
from src.infrastructure.persistence.sqlalchemy.models.user_role_model import UserRoleModel
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

LOGGER = logging.getLogger("api.admin_users")

router = APIRouter(prefix="/admin", tags=["admin"])


class FieldInfo(BaseModel):
    field_code: str
    block_no: str
    parcel_no: str
    village: str
    crop_type: str | None = None
    area_donum: float | None = None


class AdminUserResponse(BaseModel):
    user_id: str
    phone: str
    display_name: str
    province: str
    district: str
    active: bool
    fields: list[FieldInfo]


def _require_admin(request: Request) -> None:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if "admin" not in roles and "CENTRAL_ADMIN" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(request: Request) -> list[AdminUserResponse]:
    """List farmer users with their field/parcel info (admin only)."""
    _require_admin(request)

    async with get_async_session() as session:
        result = await session.execute(select(UserModel).options(selectinload(UserModel.roles)))
        models = result.scalars().unique().all()

        # Only FARMER_SINGLE users — exclude anyone with an admin/system role
        _PROTECTED_ROLES = {"CENTRAL_ADMIN", "BILLING_ADMIN", "IL_OPERATOR", "STATION_OPERATOR"}
        farmer_models = [
            m
            for m in models
            if any(r.role == "FARMER_SINGLE" for r in m.roles) and not any(r.role in _PROTECTED_ROLES for r in m.roles)
        ]

        # Batch load fields for all farmer user_ids
        farmer_ids = [m.user_id for m in farmer_models]
        field_result = (
            await session.execute(select(FieldModel).where(FieldModel.user_id.in_(farmer_ids))) if farmer_ids else None
        )
        field_rows = field_result.scalars().all() if field_result else []

    # Group fields by user_id
    fields_by_user: dict[_uuid.UUID, list[FieldInfo]] = {}
    for f in field_rows:
        info = FieldInfo(
            field_code=f.field_code,
            block_no=f.block_no,
            parcel_no=f.parcel_no,
            village=f.village,
            crop_type=f.crop_type,
            area_donum=float(f.area_donum) if f.area_donum is not None else None,
        )
        fields_by_user.setdefault(f.user_id, []).append(info)

    return [
        AdminUserResponse(
            user_id=str(m.user_id),
            phone=m.phone,
            display_name=m.display_name or f"{m.first_name} {m.last_name}".strip() or "",
            province=m.province or "",
            district=m.district or "",
            active=m.is_active,
            fields=fields_by_user.get(m.user_id, []),
        )
        for m in farmer_models
    ]


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(request: Request, user_id: str) -> None:
    """Delete a user (admin only)."""
    _require_admin(request)

    try:
        uid = _uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid user_id") from None

    _PROTECTED_ROLES = {"CENTRAL_ADMIN", "BILLING_ADMIN", "IL_OPERATOR", "STATION_OPERATOR"}

    async with get_async_session() as session:
        result = await session.execute(
            select(UserModel).options(selectinload(UserModel.roles)).where(UserModel.user_id == uid)
        )
        user_model = result.scalar_one_or_none()
        if user_model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Prevent deleting admin/operator accounts
        if any(r.role in _PROTECTED_ROLES for r in user_model.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin ve operator hesaplari silinemez.",
            )

        await session.execute(sa_delete(UserRoleModel).where(UserRoleModel.user_id == uid))
        await session.delete(user_model)
        await session.commit()

    LOGGER.info("USER.DELETED user_id=%s", user_id)
