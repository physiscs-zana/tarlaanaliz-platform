# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033: Public pricing endpoints.
"""Pricing endpoints for active snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/pricing", tags=["pricing"])


class PriceSnapshotResponse(BaseModel):
    snapshot_id: str
    version: str
    currency: str
    effective_at: datetime
    crop_type: str | None = None
    price_per_donum: float | None = None
    valid_from: str | None = None
    valid_until: str | None = None


class PriceSnapshotListResponse(BaseModel):
    items: list[PriceSnapshotResponse]


class PricingService(Protocol):
    def list_active(self, region: str | None, limit: int) -> PriceSnapshotListResponse: ...


@dataclass(slots=True)
class _InMemoryPricingService:
    def list_active(self, region: str | None, limit: int) -> PriceSnapshotListResponse:
        _ = region
        return PriceSnapshotListResponse(
            items=[
                PriceSnapshotResponse(
                    snapshot_id="ps-1",
                    version="v1",
                    currency="TRY",
                    effective_at=datetime.utcnow(),
                )
            ][:limit]
        )


def get_pricing_service(request: Request) -> PricingService:
    services = getattr(request.app.state, "services", None)
    if services is not None:
        svc = services.get("pricing_service")
        if svc is not None:
            return cast(PricingService, svc)
    return _InMemoryPricingService()


def _require_authenticated(request: Request) -> None:
    if getattr(request.state, "user", None) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


@router.get("/active", response_model=PriceSnapshotListResponse)
def list_active_pricing(
    request: Request,
    region: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=20, ge=1, le=100),
    service: PricingService = Depends(get_pricing_service),
) -> PriceSnapshotListResponse:
    # KR-081: explicit response contract for PWA pricing list.
    _require_authenticated(request)
    return service.list_active(region=region, limit=limit)


@router.get("/crops")
def get_crop_prices(request: Request) -> dict[str, object]:
    """Public crop prices from admin pricing config. KR-033."""
    _require_authenticated(request)
    from src.presentation.api.v1.endpoints.admin_pricing import _read_config

    cfg = _read_config()
    return {"crops": cfg.get("crops", []), "currency": "TRY"}
