# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-063: Admin user listing — farmers with field/parcel info.
"""Admin user management endpoints."""

from __future__ import annotations

import logging
import uuid as _uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.orm import selectinload

from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel
from src.infrastructure.persistence.sqlalchemy.models.mission_model import MissionModel
from src.infrastructure.persistence.sqlalchemy.models.payment_intent_model import PaymentIntentModel
from src.infrastructure.persistence.sqlalchemy.models.price_snapshot_model import PriceSnapshotModel
from src.infrastructure.persistence.sqlalchemy.models.subscription_model import SubscriptionModel
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
    """Delete a farmer user and all dependent records (admin only).

    Deletion order (FK-safe):
      1. Block if active/pending payment records exist (financial audit)
      2. Block if completed payment records exist (RESTRICT constraint)
      3. Delete missions referencing user's fields or requested by user
      4. Delete subscriptions for user's fields or by user
      5. SET NULL on nullable FK references (price_snapshots, granted_by, pilot assignment)
      6. Delete user → CASCADE handles: fields, user_roles, experts, pilots
    """
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

        # --- Step 1-2: Check payment records (payer_user_id has ondelete=RESTRICT) ---
        pay_result = await session.execute(select(PaymentIntentModel).where(PaymentIntentModel.payer_user_id == uid))
        payments = pay_result.scalars().all()
        if payments:
            active_statuses = {"PAYMENT_PENDING", "PENDING_ADMIN_REVIEW"}
            active_count = sum(1 for p in payments if p.status in active_statuses)
            if active_count:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Bu ciftcinin {active_count} aktif/bekleyen odeme kaydi var. "
                    f"Once odemeleri cozumleyin (onayla, reddet veya iptal edin).",
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Bu ciftcinin {len(payments)} odeme kaydi var. "
                f"Odeme gecmisi olan ciftciler veri butunlugu icin silinemez.",
            )

        # --- Step 3-4: Collect user's field_ids for cascading cleanup ---
        field_ids_result = await session.execute(select(FieldModel.field_id).where(FieldModel.user_id == uid))
        field_ids = [row[0] for row in field_ids_result.all()]

        # Delete missions referencing user or user's fields (no ondelete on FK)
        await session.execute(sa_delete(MissionModel).where(MissionModel.requested_by_user_id == uid))
        if field_ids:
            await session.execute(sa_delete(MissionModel).where(MissionModel.field_id.in_(field_ids)))

        # Delete subscriptions for user or user's fields (no ondelete on FK)
        await session.execute(sa_delete(SubscriptionModel).where(SubscriptionModel.farmer_user_id == uid))
        if field_ids:
            await session.execute(sa_delete(SubscriptionModel).where(SubscriptionModel.field_id.in_(field_ids)))

        # --- Step 5: SET NULL on nullable FK references ---
        await session.execute(
            sa_update(PriceSnapshotModel).where(PriceSnapshotModel.created_by == uid).values(created_by=None)
        )
        await session.execute(sa_update(UserRoleModel).where(UserRoleModel.granted_by == uid).values(granted_by=None))

        # --- Step 6: Delete user (CASCADE handles fields, roles, expert, pilot) ---
        await session.execute(sa_delete(UserRoleModel).where(UserRoleModel.user_id == uid))
        await session.delete(user_model)
        await session.commit()

    LOGGER.warning("USER.DELETED user_id=%s by admin", user_id)
