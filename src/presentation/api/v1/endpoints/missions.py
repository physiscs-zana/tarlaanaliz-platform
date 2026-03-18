# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015: Mission management endpoints.
"""Mission management endpoints."""

from __future__ import annotations

import uuid as _uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/missions", tags=["missions"])


class MissionCreateRequest(BaseModel):
    field_id: str = Field(min_length=3, max_length=64)
    mission_date: date
    crop_type: str = Field(default="PAMUK", min_length=2, max_length=50)
    analysis_type: str = Field(default="MULTISPECTRAL", min_length=2, max_length=50)


class MissionResponse(BaseModel):
    mission_id: str
    field_id: str
    mission_date: date
    status: str
    pilot_id: str | None = None
    subscription_id: str | None = None


def _require_authenticated(request: Request) -> tuple[str, str | None]:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    subject = str(getattr(user, "subject", ""))
    user_id = getattr(user, "user_id", None)
    return subject, user_id


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(request: Request, payload: MissionCreateRequest) -> MissionResponse:
    subject, user_id_str = _require_authenticated(request)

    from src.infrastructure.persistence.sqlalchemy.session import get_async_session
    from src.infrastructure.persistence.sqlalchemy.repositories.mission_repository_impl import MissionRepositoryImpl

    mission_id = _uuid.uuid4()
    user_id = _uuid.UUID(user_id_str) if user_id_str and len(user_id_str) > 8 else _uuid.uuid4()
    try:
        field_id = _uuid.UUID(payload.field_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="field_id must be a valid UUID")
    planned_at = datetime(
        payload.mission_date.year, payload.mission_date.month, payload.mission_date.day, tzinfo=timezone.utc
    )

    async with get_async_session() as session:
        repo = MissionRepositoryImpl(session)
        await repo.save(
            mission_id=mission_id,
            field_id=field_id,
            user_id=user_id,
            crop_type=payload.crop_type,
            analysis_type=payload.analysis_type,
            planned_at=planned_at,
        )
        await session.commit()

    return MissionResponse(
        mission_id=str(mission_id),
        field_id=payload.field_id,
        mission_date=payload.mission_date,
        status="PLANNED",
    )


@router.get("", response_model=list[MissionResponse])
async def list_missions(request: Request) -> list[MissionResponse]:
    subject, user_id_str = _require_authenticated(request)

    from src.infrastructure.persistence.sqlalchemy.session import get_async_session
    from src.infrastructure.persistence.sqlalchemy.repositories.mission_repository_impl import MissionRepositoryImpl

    try:
        user_id = _uuid.UUID(user_id_str) if user_id_str else None
    except (ValueError, TypeError):
        user_id = None

    if not user_id:
        return []

    async with get_async_session() as session:
        repo = MissionRepositoryImpl(session)
        models = await repo.list_by_user_id(user_id)

    return [
        MissionResponse(
            mission_id=str(m.mission_id),
            field_id=str(m.field_id),
            mission_date=(m.planned_at or m.created_at).date(),
            status=m.status,
        )
        for m in models
    ]
