# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-012: Duyuru endpoint'leri — uçuş başlangıç tarihi, kampanya, genel bildirimler.
"""Announcement endpoints — CENTRAL_ADMIN creates, farmers/pilots see."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.infrastructure.persistence.sqlalchemy.models.announcement_model import AnnouncementModel
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

router = APIRouter(prefix="/announcements", tags=["announcements"])


class AnnouncementCreateRequest(BaseModel):
    announcement_type: str = Field(pattern="^(FLIGHT_START|CAMPAIGN|GENERAL|MAINTENANCE)$")
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=3, max_length=2000)
    target_date: datetime | None = None
    target_roles: str | None = Field(default=None, max_length=200)
    target_province: str | None = Field(default=None, max_length=100)
    visible_from: datetime | None = None
    visible_until: datetime | None = None


class AnnouncementResponse(BaseModel):
    announcement_id: str
    announcement_type: str
    title: str
    body: str
    target_date: str | None
    target_province: str | None
    visible_from: str
    visible_until: str | None
    created_at: str


def _require_admin(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if "CENTRAL_ADMIN" not in roles and "admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return str(getattr(user, "subject", ""))


def _require_auth(request: Request) -> tuple[str, set[str]]:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    return str(getattr(user, "subject", "")), roles


def _model_to_response(m: AnnouncementModel) -> AnnouncementResponse:
    return AnnouncementResponse(
        announcement_id=str(m.announcement_id),
        announcement_type=m.announcement_type,
        title=m.title,
        body=m.body,
        target_date=m.target_date.isoformat() if m.target_date else None,
        target_province=m.target_province,
        visible_from=m.visible_from.isoformat(),
        visible_until=m.visible_until.isoformat() if m.visible_until else None,
        created_at=m.created_at.isoformat(),
    )


@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(request: Request, payload: AnnouncementCreateRequest) -> AnnouncementResponse:
    """Duyuru oluştur — sadece CENTRAL_ADMIN."""
    admin_id = _require_admin(request)

    async with get_async_session() as session:
        model = AnnouncementModel()
        model.announcement_type = payload.announcement_type
        model.title = payload.title
        model.body = payload.body
        model.target_date = payload.target_date
        model.target_roles = payload.target_roles
        model.target_province = payload.target_province
        model.visible_from = payload.visible_from or datetime.now(timezone.utc)
        model.visible_until = payload.visible_until
        session.add(model)
        await session.commit()
        await session.refresh(model)
        return _model_to_response(model)


@router.get("", response_model=list[AnnouncementResponse])
async def list_announcements(
    request: Request,
    announcement_type: str | None = Query(default=None),
    province: str | None = Query(default=None),
) -> list[AnnouncementResponse]:
    """Aktif duyuruları listele — kullanıcı rolüne göre filtreli."""
    user_id, user_roles = _require_auth(request)
    now = datetime.now(timezone.utc)

    async with get_async_session() as session:
        stmt = select(AnnouncementModel).where(
            AnnouncementModel.is_active.is_(True),
            AnnouncementModel.visible_from <= now,
        )
        if announcement_type:
            stmt = stmt.where(AnnouncementModel.announcement_type == announcement_type)
        if province:
            stmt = stmt.where(
                (AnnouncementModel.target_province.is_(None)) | (AnnouncementModel.target_province == province)
            )

        result = await session.execute(stmt.order_by(AnnouncementModel.created_at.desc()).limit(50))
        models = result.scalars().all()

        # Rol filtresi: target_roles boşsa herkese, doluysa sadece eşleşenlere
        filtered = []
        for m in models:
            if m.visible_until and m.visible_until < now:
                continue
            if m.target_roles:
                target = {r.strip() for r in m.target_roles.split(",")}
                if not target.intersection(user_roles):
                    continue
            filtered.append(_model_to_response(m))

        return filtered
