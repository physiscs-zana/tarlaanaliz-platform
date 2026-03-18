# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: Admin pricing snapshot management.
"""Admin pricing snapshot publish endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, cast

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
    def publish_snapshot(
        self, payload: PublishPricingSnapshotRequest, actor_subject: str
    ) -> PublishPricingSnapshotResponse: ...


@dataclass(slots=True)
class _InMemoryAdminPricingService:
    def publish_snapshot(
        self, payload: PublishPricingSnapshotRequest, actor_subject: str
    ) -> PublishPricingSnapshotResponse:
        _ = actor_subject
        return PublishPricingSnapshotResponse(snapshot_id=payload.snapshot_id, published=True)


def get_admin_pricing_service(request: Request) -> AdminPricingService:
    services = getattr(request.app.state, "services", None)
    if services is not None:
        svc = services.get("admin_pricing_service")
        if svc is not None:
            return cast(AdminPricingService, svc)
    return _InMemoryAdminPricingService()


def _require_admin(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if "admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return str(getattr(user, "subject", ""))


_CONFIG_PATH = "/app/data/pricing_config.json"
_CONFIG_PATH_LOCAL = "data/pricing_config.json"


def _config_path() -> str:
    import os

    return _CONFIG_PATH if os.path.exists(_CONFIG_PATH) else _CONFIG_PATH_LOCAL


def _read_config() -> dict[str, object]:
    import json
    import os

    path = _config_path()
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def _write_config(data: dict[str, object]) -> None:
    import json
    import os

    path = _config_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class PricingConfigRequest(BaseModel):
    iban: str = Field(max_length=40)
    bank_name: str = Field(max_length=80)
    recipient: str = Field(max_length=120)
    crops: list[dict[str, object]] = Field(default_factory=list)


@router.get("/config")
def get_pricing_config(request: Request) -> dict[str, object]:
    """Return full pricing config (IBAN + crop prices). Admin only."""
    _require_admin(request)
    return _read_config()


@router.put("/config")
def update_pricing_config(request: Request, payload: PricingConfigRequest) -> dict[str, str]:
    """Update pricing config (IBAN + crop prices). Admin only."""
    _require_admin(request)
    _write_config(payload.model_dump())
    return {"status": "saved"}


@router.get("/info")
def get_pricing_info(request: Request) -> dict[str, object]:
    """Return basic pricing configuration. IBAN-only payment (KR-033)."""
    _require_admin(request)
    return {
        "payment_method": "IBAN_TRANSFER",
        "currency": "TRY",
        "notes": "Odeme yalnizca IBAN havale ile yapilir. Fatura kesilir.",
        "snapshots": [],
    }


@router.post("/snapshot/publish", response_model=PublishPricingSnapshotResponse, status_code=status.HTTP_201_CREATED)
def publish_pricing_snapshot(
    request: Request,
    payload: PublishPricingSnapshotRequest,
    service: AdminPricingService = Depends(get_admin_pricing_service),
) -> PublishPricingSnapshotResponse:
    # KR-081: contract-first request/response DTO boundary.
    actor_subject = _require_admin(request)
    return service.publish_snapshot(payload=payload, actor_subject=actor_subject)
