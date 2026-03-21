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
from src.infrastructure.persistence.sqlalchemy.models.pilot_model import (
    PilotModel,
    PilotServiceAreaModel,
)
from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
from src.infrastructure.persistence.sqlalchemy.repositories.user_repository_impl import UserRepositoryImpl
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

LOGGER = logging.getLogger("api.pilots")

router = APIRouter(prefix="/pilots", tags=["pilots"])


class PilotCapacityResponse(BaseModel):
    work_days: list[str]
    daily_capacity_donum: int


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
    from sqlalchemy import select
    from src.infrastructure.persistence.sqlalchemy.models.user_role_model import UserRoleModel

    async with get_async_session() as session:
        result = await session.execute(
            select(UserModel)
            .join(UserRoleModel, UserModel.user_id == UserRoleModel.user_id)
            .where(UserRoleModel.role == UserRole.PILOT.value)
        )
        models = result.scalars().unique().all()
    return [
        PilotResponse(
            user_id=str(m.user_id),
            phone=m.phone,
            display_name=m.display_name or f"{m.first_name} {m.last_name}".strip() or "",
            province=m.province or "",
            role=UserRole.PILOT.value,
            active=m.is_active,
        )
        for m in models
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

        # Save display_name to user model
        from sqlalchemy import select

        result = await session.execute(select(UserModel).where(UserModel.user_id == user.user_id))
        user_model = result.scalar_one_or_none()
        if user_model:
            user_model.display_name = payload.display_name

        # Create PilotModel + PilotServiceAreaModel for auto-dispatch
        pilot_id = _uuid.uuid4()
        drone_serial = f"DRONE-{_uuid.uuid4().hex[:8].upper()}"
        pilot = PilotModel(
            pilot_id=pilot_id,
            user_id=user.user_id,
            province=payload.province,
            drone_serial_no=drone_serial,
        )
        session.add(pilot)
        await session.flush()

        service_area = PilotServiceAreaModel(
            service_area_id=_uuid.uuid4(),
            pilot_id=pilot_id,
            province=payload.province,
            district="",
        )
        session.add(service_area)
        await session.commit()

    LOGGER.warning("PILOT.CREATED user_id=%s pilot_id=%s province=%s", user.user_id, pilot_id, payload.province)
    return PilotResponse(
        user_id=str(user.user_id),
        phone=payload.phone,
        display_name=payload.display_name,
        province=payload.province,
        role=UserRole.PILOT.value,
    )


class PilotCapacityUpdateRequest(BaseModel):
    work_days: list[str] = Field(min_length=1, max_length=6)
    daily_capacity_donum: int = Field(ge=2500, le=3000)


class PilotDroneResponse(BaseModel):
    drone_model: str = ""
    drone_serial: str = ""
    sensor_type: str = ""
    locked: bool = False


class PilotDroneUpdateRequest(BaseModel):
    drone_model: str = Field(min_length=1, max_length=100)
    drone_serial: str = Field(min_length=1, max_length=100)
    sensor_type: str = Field(default="", max_length=100)


def _get_pilot_user_id(request: Request) -> _uuid.UUID:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    uid = getattr(user, "user_id", None) or getattr(user, "subject", None)
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return _uuid.UUID(str(uid))


@router.get("/me/capacity")
async def get_my_capacity(request: Request) -> dict[str, object]:
    """KR-015: Get pilot's capacity — from pilots table if exists, else defaults."""
    user_id = _get_pilot_user_id(request)
    from sqlalchemy import select
    from src.infrastructure.persistence.sqlalchemy.models.pilot_model import PilotModel

    async with get_async_session() as session:
        result = await session.execute(select(PilotModel).where(PilotModel.user_id == user_id))
        pilot = result.scalar_one_or_none()

    if pilot:
        return {
            "work_days": pilot.work_days or [],
            "daily_capacity_donum": pilot.daily_capacity_donum,
            "locked": len(pilot.work_days or []) > 0,
        }

    return {"work_days": [], "daily_capacity_donum": 2750, "locked": False}


@router.put("/me/capacity")
async def update_my_capacity(request: Request, payload: PilotCapacityUpdateRequest) -> dict[str, object]:
    """KR-015: Save pilot capacity (one-time). Creates pilot record if needed."""
    user_id = _get_pilot_user_id(request)
    from sqlalchemy import select
    from src.infrastructure.persistence.sqlalchemy.models.pilot_model import PilotModel

    async with get_async_session() as session:
        result = await session.execute(select(PilotModel).where(PilotModel.user_id == user_id))
        pilot = result.scalar_one_or_none()

        if pilot:
            if len(pilot.work_days or []) > 0:
                raise HTTPException(
                    status_code=409, detail="Plan zaten kaydedildi. Degisiklik icin Central Admin'e basvurun."
                )
            pilot.work_days = payload.work_days
            pilot.daily_capacity_donum = payload.daily_capacity_donum
            pilot.updated_at = datetime.now(timezone.utc)
        else:
            # Auto-create pilot record
            pilot = PilotModel(
                user_id=user_id,
                drone_model="",
                drone_serial_no=f"AUTO-{_uuid.uuid4().hex[:8]}",
                province="",
                work_days=payload.work_days,
                daily_capacity_donum=payload.daily_capacity_donum,
            )
            session.add(pilot)
        await session.commit()

    LOGGER.warning(
        "PILOT.CAPACITY_SAVED user=%s days=%s capacity=%d", user_id, payload.work_days, payload.daily_capacity_donum
    )
    return {"work_days": payload.work_days, "daily_capacity_donum": payload.daily_capacity_donum, "locked": True}


@router.get("/me/drone")
async def get_my_drone(request: Request) -> dict[str, object]:
    """Get pilot's drone info + profile from pilots table."""
    user_id = _get_pilot_user_id(request)
    from sqlalchemy import select
    from src.infrastructure.persistence.sqlalchemy.models.pilot_model import PilotModel

    display_name = ""
    province = ""

    async with get_async_session() as session:
        # Get user display_name and province
        user_result = await session.execute(select(UserModel).where(UserModel.user_id == user_id))
        user_model = user_result.scalar_one_or_none()
        if user_model:
            display_name = user_model.display_name or f"{user_model.first_name} {user_model.last_name}".strip()
            province = user_model.province or ""

        result = await session.execute(select(PilotModel).where(PilotModel.user_id == user_id))
        pilot = result.scalar_one_or_none()

    base = {"display_name": display_name, "province": province}
    if pilot and pilot.drone_model:
        return {
            **base,
            "drone_model": pilot.drone_model,
            "drone_serial": pilot.drone_serial_no,
            "sensor_type": "",
            "locked": True,
        }

    return {**base, "drone_model": "", "drone_serial": "", "sensor_type": "", "locked": False}


@router.put("/me/drone")
async def update_my_drone(request: Request, payload: PilotDroneUpdateRequest) -> dict[str, object]:
    """Save pilot drone info (one-time). Creates pilot record if needed."""
    user_id = _get_pilot_user_id(request)
    from sqlalchemy import select
    from src.infrastructure.persistence.sqlalchemy.models.pilot_model import PilotModel

    async with get_async_session() as session:
        result = await session.execute(select(PilotModel).where(PilotModel.user_id == user_id))
        pilot = result.scalar_one_or_none()

        if pilot:
            if pilot.drone_model and pilot.drone_model != "":
                raise HTTPException(
                    status_code=409,
                    detail="Drone bilgileri zaten kaydedildi. Degisiklik icin Central Admin'e basvurun.",
                )
            pilot.drone_model = payload.drone_model
            pilot.drone_serial_no = payload.drone_serial
            pilot.updated_at = datetime.now(timezone.utc)
        else:
            pilot = PilotModel(
                user_id=user_id,
                drone_model=payload.drone_model,
                drone_serial_no=payload.drone_serial,
                province="",
                work_days=[],
                daily_capacity_donum=2750,
            )
            session.add(pilot)
        await session.commit()

    LOGGER.warning("PILOT.DRONE_SAVED user=%s model=%s serial=%s", user_id, payload.drone_model, payload.drone_serial)
    return {
        "drone_model": payload.drone_model,
        "drone_serial": payload.drone_serial,
        "sensor_type": payload.sensor_type,
        "locked": True,
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pilot(request: Request, user_id: str) -> None:
    """Delete a pilot user (admin only)."""
    _require_admin(request)
    from sqlalchemy import select, delete as sa_delete
    from src.infrastructure.persistence.sqlalchemy.models.user_role_model import UserRoleModel

    try:
        uid = _uuid.UUID(user_id)
    except ValueError as err:
        raise HTTPException(status_code=422, detail="Invalid user_id") from err

    async with get_async_session() as session:
        result = await session.execute(select(UserModel).where(UserModel.user_id == uid))
        user_model = result.scalar_one_or_none()
        if user_model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pilot not found")

        await session.execute(sa_delete(UserRoleModel).where(UserRoleModel.user_id == uid))
        await session.delete(user_model)
        await session.commit()

    LOGGER.info("PILOT.DELETED user_id=%s", user_id)
