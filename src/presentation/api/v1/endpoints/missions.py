# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
"""Mission management endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/missions", tags=["missions"])


class MissionCreateRequest(BaseModel):
    field_id: str = Field(min_length=3, max_length=64)
    mission_date: date
    pilot_id: str | None = Field(default=None, min_length=3, max_length=64)


class MissionResponse(BaseModel):
    mission_id: str
    field_id: str
    mission_date: date
    status: str


class MissionService(Protocol):
    def create(self, payload: MissionCreateRequest, actor_subject: str) -> MissionResponse:
        ...

    def list_for_subject(self, actor_subject: str) -> list[MissionResponse]:
        ...


@dataclass(slots=True)
class _InMemoryMissionService:
    def create(self, payload: MissionCreateRequest, actor_subject: str) -> MissionResponse:
        _ = actor_subject
        # KR-015: planning and capacity rules are enforced in application/domain service layer.
        return MissionResponse(mission_id="msn-1", field_id=payload.field_id, mission_date=payload.mission_date, status="planned")

    def list_for_subject(self, actor_subject: str) -> list[MissionResponse]:
        _ = actor_subject
        return []


def get_mission_service() -> MissionService:
    return _InMemoryMissionService()


def _require_authenticated_subject(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return str(getattr(user, "subject", ""))


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
def create_mission(
    request: Request,
    payload: MissionCreateRequest,
    service: MissionService = Depends(get_mission_service),
) -> MissionResponse:
    subject = _require_authenticated_subject(request)
    return service.create(payload=payload, actor_subject=subject)


@router.get("", response_model=list[MissionResponse])
def list_missions(request: Request, service: MissionService = Depends(get_mission_service)) -> list[MissionResponse]:
    subject = _require_authenticated_subject(request)
    return service.list_for_subject(actor_subject=subject)
