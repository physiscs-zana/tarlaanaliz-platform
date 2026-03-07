# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-013: Parcel lookup endpoints.
"""Parcel lookup endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/parcels", tags=["parcels"])


class GeometryDTO(BaseModel):
    type: str = Field(default="Polygon")
    coordinates: list[list[list[float]]]


class ParcelLookupResponse(BaseModel):
    parcel_ref: str
    geometry: GeometryDTO
    provider: str


class ParcelLookupService(Protocol):
    def lookup_geometry(self, parcel_ref: str) -> ParcelLookupResponse: ...


@dataclass(slots=True)
class _InMemoryParcelLookupService:
    def lookup_geometry(self, parcel_ref: str) -> ParcelLookupResponse:
        return ParcelLookupResponse(
            parcel_ref=parcel_ref,
            provider="mock-tkgm",
            geometry=GeometryDTO(coordinates=[[[29.0, 41.0], [29.1, 41.0], [29.1, 41.1], [29.0, 41.0]]]),
        )


def get_parcel_lookup_service(request: Request) -> ParcelLookupService:
    services = getattr(request.app.state, "services", None)
    if services is not None:
        svc = services.get("parcel_lookup_service")
        if svc is not None:
            return cast(ParcelLookupService, svc)
    return _InMemoryParcelLookupService()


def _require_authenticated(request: Request) -> None:
    if getattr(request.state, "user", None) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


@router.get("/lookup", response_model=ParcelLookupResponse)
def lookup_parcel(
    request: Request,
    parcel_ref: str = Query(min_length=3, max_length=64),
    service: ParcelLookupService = Depends(get_parcel_lookup_service),
) -> ParcelLookupResponse:
    _require_authenticated(request)
    return service.lookup_geometry(parcel_ref=parcel_ref)
