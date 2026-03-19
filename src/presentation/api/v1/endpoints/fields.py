# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: Field CRUD endpoints.
"""Field CRUD endpoints."""

from __future__ import annotations

import logging
import re
import uuid as _uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from src.core.domain.entities.field import Field as FieldEntity
from src.core.domain.entities.field import FieldStatus
from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel
from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
from src.infrastructure.persistence.sqlalchemy.repositories.field_repository_impl import (
    FieldRepositoryImpl,
)
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

LOGGER = logging.getLogger("api.fields")

router = APIRouter(prefix="/fields", tags=["fields"])

# SEC: XSS sanitization — strip HTML/script injection from user inputs
_XSS_PATTERN = re.compile(r"[<>]|javascript:|on\w+\s*=", re.IGNORECASE)


def _sanitize(value: str) -> str:
    return _XSS_PATTERN.sub("", value).strip()


class FieldCreateRequest(BaseModel):
    field_name: str | None = Field(default=None, max_length=120)
    parcel_ref: str = Field(min_length=3, max_length=64)
    area_ha: float = Field(gt=0)
    crop_type: str | None = Field(default=None, max_length=50)

    @field_validator("parcel_ref", "crop_type", "field_name", mode="before")
    @classmethod
    def strip_xss(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _sanitize(v)


class FieldResponse(BaseModel):
    field_id: str
    field_code: str
    field_name: str
    parcel_ref: str
    area_ha: float
    crop_type: str | None = None


class FieldListResponse(BaseModel):
    items: list[FieldResponse]


def _get_user_uuid(request: Request) -> _uuid.UUID:
    """Extract and validate user UUID from JWT.

    Tries request.state.user.user_id first, falls back to subject.
    Raises 401 if user is not authenticated or ID is not a valid UUID.
    """
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    # Try user_id first (set by JwtMiddleware from JWT claims)
    user_id_str = getattr(user, "user_id", None)
    if not user_id_str:
        user_id_str = getattr(user, "subject", None)

    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum bilgisi eksik. Lutfen tekrar giris yapin.",
        )

    try:
        return _uuid.UUID(str(user_id_str))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gecersiz oturum. Lutfen tekrar giris yapin.",
        ) from None


@router.post("", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
async def create_field(request: Request, payload: FieldCreateRequest) -> FieldResponse:
    user_uuid = _get_user_uuid(request)

    # Validate parcel_ref format
    parts = payload.parcel_ref.split("/")
    if len(parts) != 5 or any(not p.strip() for p in parts):
        raise HTTPException(
            status_code=422,
            detail="parcel_ref must be in format: il/ilce/mahalle/ada/parsel",
        )
    province, district, village, ada, parsel = [p.strip() for p in parts]

    # Validate no empty fields after sanitization
    for name, val in [
        ("il", province),
        ("ilce", district),
        ("mahalle", village),
        ("ada", ada),
        ("parsel", parsel),
    ]:
        if not val:
            raise HTTPException(status_code=422, detail=f"{name} alani bos olamaz.")

    field_name = payload.field_name or f"{village} {ada}/{parsel}"
    area_m2 = Decimal(str(payload.area_ha)) * Decimal("10000")

    # SINGLE session: user check + field save in one transaction
    async with get_async_session() as session:
        # 1. Verify user exists
        result = await session.execute(select(UserModel.user_id).where(UserModel.user_id == user_uuid))
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kullanici bulunamadi. Lutfen tekrar giris yapin.",
            )

        # 2. Create entity (validates invariants)
        now = datetime.now(timezone.utc)
        try:
            field = FieldEntity(
                field_id=_uuid.uuid4(),
                user_id=user_uuid,
                province=province,
                district=district,
                village=village,
                ada=ada,
                parsel=parsel,
                area_m2=area_m2,
                status=FieldStatus.ACTIVE,
                created_at=now,
                updated_at=now,
                crop_type=payload.crop_type,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None

        # 3. Save to DB
        try:
            repo = FieldRepositoryImpl(session)
            await repo.save(field)
            await session.commit()
        except Exception as exc:
            exc_str = str(exc).lower()
            LOGGER.error("FIELD.CREATE_FAILED user_id=%s error=%s", user_uuid, exc)
            if "uq_field_parcel" in exc_str:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Bu ada/parsel zaten kayitli.",
                ) from None
            if "foreign key" in exc_str or "violates foreign key" in exc_str:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Gecersiz kullanici. Lutfen tekrar giris yapin.",
                ) from None
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Tarla kaydedilemedi: {type(exc).__name__}",
            ) from None

    # Fetch DB-generated field_code (server_default from sequence)
    async with get_async_session() as session:
        result = await session.execute(
            select(FieldModel.field_code).where(FieldModel.field_id == field.field_id)
        )
        field_code = result.scalar_one()

    return FieldResponse(
        field_id=str(field.field_id),
        field_code=field_code,
        field_name=field_name,
        parcel_ref=payload.parcel_ref,
        area_ha=payload.area_ha,
        crop_type=payload.crop_type,
    )


@router.get("", response_model=FieldListResponse)
async def list_fields(request: Request) -> FieldListResponse:
    try:
        user_uuid = _get_user_uuid(request)
    except HTTPException:
        return FieldListResponse(items=[])

    async with get_async_session() as session:
        repo = FieldRepositoryImpl(session)
        fields = await repo.list_by_user_id(user_uuid)

    return FieldListResponse(
        items=[
            FieldResponse(
                field_id=str(f.field_id),
                field_code=f.field_code or "",
                field_name=f"{f.village} {f.ada}/{f.parsel}",
                parcel_ref=f.parcel_ref,
                area_ha=float(f.area_m2 / Decimal("10000")),
                crop_type=f.crop_type,
            )
            for f in fields
        ]
    )
