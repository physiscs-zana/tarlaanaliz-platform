# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Expert management endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/experts", tags=["experts"])


class ExpertCreateRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    expertise_tags: list[str] = Field(default_factory=list, max_length=20)


class ExpertResponse(BaseModel):
    expert_id: str
    display_name: str
    expertise_tags: list[str]
    active: bool


class ExpertService(Protocol):
    def create(self, payload: ExpertCreateRequest) -> ExpertResponse: ...

    def list_all(self) -> list[ExpertResponse]: ...


@dataclass(slots=True)
class _InMemoryExpertService:
    def create(self, payload: ExpertCreateRequest) -> ExpertResponse:
        return ExpertResponse(
            expert_id="exp-1", display_name=payload.display_name, expertise_tags=payload.expertise_tags, active=True
        )

    def list_all(self) -> list[ExpertResponse]:
        return [ExpertResponse(expert_id="exp-1", display_name="Demo Expert", expertise_tags=["crop"], active=True)]


def get_expert_service() -> ExpertService:
    return _InMemoryExpertService()


def _require_admin(request: Request) -> None:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    if "admin" not in set(getattr(request.state, "roles", [])):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("", response_model=ExpertResponse, status_code=status.HTTP_201_CREATED)
def create_expert(
    request: Request,
    payload: ExpertCreateRequest,
    service: ExpertService = Depends(get_expert_service),
) -> ExpertResponse:
    _require_admin(request)
    return service.create(payload)


@router.get("", response_model=list[ExpertResponse])
def list_experts(request: Request, service: ExpertService = Depends(get_expert_service)) -> list[ExpertResponse]:
    _require_admin(request)
    return service.list_all()
