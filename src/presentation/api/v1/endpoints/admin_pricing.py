# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Admin pricing snapshot publish endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/admin/pricing", tags=["admin-pricing"])


class PublishPricingSnapshotRequest(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=64)
    version: str = Field(min_length=1, max_length=32)
    effective_at: datetime
    currency: str = Field(min_length=3, max_length=3)
    notes: str | None = Field(default=None, max_length=256)


class PublishPricingSnapshotResponse(BaseModel):
    snapshot_id: str
    published: bool


class AdminPricingService(Protocol):
    def publish_snapshot(self, payload: PublishPricingSnapshotRequest, actor_subject: str) -> PublishPricingSnapshotResponse:
        ...


@dataclass(slots=True)
class _InMemoryAdminPricingService:
    def publish_snapshot(self, payload: PublishPricingSnapshotRequest, actor_subject: str) -> PublishPricingSnapshotResponse:
        _ = actor_subject
        return PublishPricingSnapshotResponse(snapshot_id=payload.snapshot_id, published=True)


def get_admin_pricing_service() -> AdminPricingService:
    return _InMemoryAdminPricingService()


def _require_admin(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if "admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return str(getattr(user, "subject", ""))


@router.post("/snapshot/publish", response_model=PublishPricingSnapshotResponse, status_code=status.HTTP_201_CREATED)
def publish_pricing_snapshot(
    request: Request,
    payload: PublishPricingSnapshotRequest,
    service: AdminPricingService = Depends(get_admin_pricing_service),
) -> PublishPricingSnapshotResponse:
    # KR-081: contract-first request/response DTO boundary.
    actor_subject = _require_admin(request)
    return service.publish_snapshot(payload=payload, actor_subject=actor_subject)
