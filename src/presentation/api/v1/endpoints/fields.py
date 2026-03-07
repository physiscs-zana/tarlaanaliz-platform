# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: Field CRUD endpoints.
"""Field CRUD endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
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


class FieldService(Protocol):
    def create(self, owner_subject: str, payload: FieldCreateRequest) -> FieldResponse: ...

    def list_by_owner(self, owner_subject: str) -> list[FieldResponse]: ...


@dataclass(slots=True)
class _InMemoryFieldService:
    def create(self, owner_subject: str, payload: FieldCreateRequest) -> FieldResponse:
        _ = owner_subject
        return FieldResponse(
            field_id="fld-1", field_name=payload.field_name, parcel_ref=payload.parcel_ref, area_ha=payload.area_ha
        )

    def list_by_owner(self, owner_subject: str) -> list[FieldResponse]:
        _ = owner_subject
        return []


def get_field_service(request: Request) -> FieldService:
    services = getattr(request.app.state, "services", None)
    if services is not None:
        svc = services.get("field_service")
        if svc is not None:
            return cast(FieldService, svc)
    return _InMemoryFieldService()


def _require_authenticated_subject(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return str(getattr(user, "subject", ""))


@router.post("", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
def create_field(
    request: Request,
    payload: FieldCreateRequest,
    service: FieldService = Depends(get_field_service),
) -> FieldResponse:
    # KR-081: explicit DTO contract at API surface.
    subject = _require_authenticated_subject(request)
    return service.create(owner_subject=subject, payload=payload)


class FieldListResponse(BaseModel):
    items: list[FieldResponse]


@router.get("", response_model=FieldListResponse)
def list_fields(request: Request, service: FieldService = Depends(get_field_service)) -> FieldListResponse:
    subject = _require_authenticated_subject(request)
    return FieldListResponse(items=service.list_by_owner(owner_subject=subject))
