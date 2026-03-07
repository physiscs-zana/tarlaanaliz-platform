# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015: Pilot management endpoints.
"""Pilot management endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/pilots", tags=["pilots"])


class PilotCreateRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    license_no: str = Field(min_length=3, max_length=32)
    regions: list[str] = Field(default_factory=list, max_length=20)


class PilotResponse(BaseModel):
    pilot_id: str
    display_name: str
    active: bool
    regions: list[str]


class PilotService(Protocol):
    def create(self, payload: PilotCreateRequest) -> PilotResponse: ...

    def list_all(self) -> list[PilotResponse]: ...


@dataclass(slots=True)
class _InMemoryPilotService:
    def create(self, payload: PilotCreateRequest) -> PilotResponse:
        return PilotResponse(pilot_id="plt-1", display_name=payload.display_name, active=True, regions=payload.regions)

    def list_all(self) -> list[PilotResponse]:
        return [PilotResponse(pilot_id="plt-1", display_name="Demo Pilot", active=True, regions=["marmara"])]


def get_pilot_service(request: Request) -> PilotService:
    services = getattr(request.app.state, "services", None)
    if services is not None:
        svc = services.get("pilot_service")
        if svc is not None:
            return cast(PilotService, svc)
    return _InMemoryPilotService()


def _require_admin(request: Request) -> None:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    if "admin" not in set(getattr(request.state, "roles", [])):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("", response_model=PilotResponse, status_code=status.HTTP_201_CREATED)
def create_pilot(
    request: Request,
    payload: PilotCreateRequest,
    service: PilotService = Depends(get_pilot_service),
) -> PilotResponse:
    _require_admin(request)
    return service.create(payload)


@router.get("", response_model=list[PilotResponse])
def list_pilots(request: Request, service: PilotService = Depends(get_pilot_service)) -> list[PilotResponse]:
    _require_admin(request)
    return service.list_all()
