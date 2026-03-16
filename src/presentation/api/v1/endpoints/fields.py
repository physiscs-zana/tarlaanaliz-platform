# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: Field CRUD endpoints.
"""Field CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/fields", tags=["fields"])


class FieldCreateRequest(BaseModel):
    field_name: str = Field(min_length=2, max_length=120)
    parcel_ref: str = Field(min_length=3, max_length=64)
    area_ha: float = Field(gt=0)


class FieldResponse(BaseModel):
    field_id: str
    field_name: str
    parcel_ref: str
    area_ha: float


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

    now = datetime.now(timezone.utc)
    field = Field(
        field_id=_uuid.uuid4(),
        user_id=_uuid.UUID(user_id_str) if len(user_id_str) > 8 else _uuid.uuid4(),
        province=payload.parcel_ref.split("/")[0] if "/" in payload.parcel_ref else "Unknown",
        district=payload.parcel_ref.split("/")[1] if payload.parcel_ref.count("/") >= 1 else "Unknown",
        village=payload.parcel_ref.split("/")[2] if payload.parcel_ref.count("/") >= 2 else "Unknown",
        ada=payload.parcel_ref.split("/")[3] if payload.parcel_ref.count("/") >= 3 else "0",
        parsel=payload.parcel_ref.split("/")[4] if payload.parcel_ref.count("/") >= 4 else "0",
        area_m2=Decimal(str(payload.area_ha)) * Decimal("10000"),
        status=FieldStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )

    async with get_async_session() as session:
        repo = FieldRepositoryImpl(session)
        await repo.save(field)
        await session.commit()

    return FieldResponse(
        field_id=str(field.field_id),
        field_name=payload.field_name,
        parcel_ref=payload.parcel_ref,
        area_ha=payload.area_ha,
    )


@router.get("", response_model=FieldListResponse)
async def list_fields(request: Request) -> FieldListResponse:
    subject = _require_authenticated_subject(request)
    user_id_str = getattr(getattr(request.state, "user", None), "user_id", None) or subject

    import uuid as _uuid
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
                field_name=f.parcel_ref,
                parcel_ref=f.parcel_ref,
                area_ha=float(f.area_m2 / 10000),
            )
            for f in fields
        ]
    )
