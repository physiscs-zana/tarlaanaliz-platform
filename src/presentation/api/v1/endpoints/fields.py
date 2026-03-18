# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: Field CRUD endpoints.
"""Field CRUD endpoints."""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

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
    field_name: str
    parcel_ref: str
    area_ha: float
    crop_type: str | None = None


def _require_authenticated_subject(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return str(getattr(user, "subject", ""))


class FieldListResponse(BaseModel):
    items: list[FieldResponse]


@router.post("", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
async def create_field(request: Request, payload: FieldCreateRequest) -> FieldResponse:
    subject = _require_authenticated_subject(request)
    user_id_str = getattr(getattr(request.state, "user", None), "user_id", None) or subject

    import uuid as _uuid
    from decimal import Decimal
    from datetime import datetime, timezone
    from src.infrastructure.persistence.sqlalchemy.session import get_async_session
    from src.infrastructure.persistence.sqlalchemy.repositories.field_repository_impl import FieldRepositoryImpl
    from src.core.domain.entities.field import Field, FieldStatus

    # H4: Validate parcel_ref format before processing
    parts = payload.parcel_ref.split("/")
    if len(parts) != 5 or any(not p.strip() for p in parts):
        raise HTTPException(
            status_code=422,
            detail="parcel_ref must be in format: il/ilce/mahalle/ada/parsel",
        )
    province, district, village, ada, parsel = [p.strip() for p in parts]

    # Auto-generate field_name from parcel_ref if not provided
    field_name = payload.field_name or f"{village} {ada}/{parsel}"

    # Resolve user_id safely — invalid UUID should not cause 500
    try:
        user_uuid = _uuid.UUID(user_id_str) if user_id_str and len(user_id_str) > 8 else _uuid.uuid4()
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz kullanıcı kimliği. Lütfen tekrar giriş yapın.",
        )

    now = datetime.now(timezone.utc)
    field = Field(
        field_id=_uuid.uuid4(),
        user_id=user_uuid,
        province=province,
        district=district,
        village=village,
        ada=ada,
        parsel=parsel,
        area_m2=Decimal(str(payload.area_ha)) * Decimal("10000"),
        status=FieldStatus.ACTIVE,
        created_at=now,
        updated_at=now,
        crop_type=payload.crop_type,
    )

    try:
        async with get_async_session() as session:
            repo = FieldRepositoryImpl(session)
            await repo.save(field)
            await session.commit()
    except Exception as exc:
        import logging

        logging.getLogger("api.fields").error("FIELD.CREATE_FAILED user_id=%s error=%s", user_uuid, exc)
        detail = "Tarla kaydedilemedi."
        if "uq_field_parcel" in str(exc):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bu ada/parsel zaten kayitli.") from exc
        if "foreign key" in str(exc).lower() or "violates foreign key" in str(exc).lower():
            detail = "Gecersiz kullanici. Lutfen tekrar giris yapin."
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc

    return FieldResponse(
        field_id=str(field.field_id),
        field_name=field_name,
        parcel_ref=payload.parcel_ref,
        area_ha=payload.area_ha,
        crop_type=payload.crop_type,
    )


@router.get("", response_model=FieldListResponse)
async def list_fields(request: Request) -> FieldListResponse:
    subject = _require_authenticated_subject(request)
    user_id_str = getattr(getattr(request.state, "user", None), "user_id", None) or subject

    import uuid as _uuid
    from decimal import Decimal
    from src.infrastructure.persistence.sqlalchemy.session import get_async_session
    from src.infrastructure.persistence.sqlalchemy.repositories.field_repository_impl import FieldRepositoryImpl

    try:
        user_uuid = _uuid.UUID(user_id_str)
    except (ValueError, AttributeError):
        return FieldListResponse(items=[])

    async with get_async_session() as session:
        repo = FieldRepositoryImpl(session)
        fields = await repo.list_by_user_id(user_uuid)

    return FieldListResponse(
        items=[
            FieldResponse(
                field_id=str(f.field_id),
                field_name=f"{f.village} {f.ada}/{f.parsel}",
                parcel_ref=f.parcel_ref,
                area_ha=float(f.area_m2 / Decimal("10000")),
                crop_type=f.crop_type,
            )
            for f in fields
        ]
    )
