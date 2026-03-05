# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Subscription purchase/view/schedule endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class SubscriptionPurchaseRequest(BaseModel):
    plan_code: str = Field(min_length=2, max_length=32)
    start_date: date


class SubscriptionResponse(BaseModel):
    subscription_id: str
    plan_code: str
    start_date: date
    status: str


class SubscriptionService(Protocol):
    def purchase(self, payload: SubscriptionPurchaseRequest, owner_subject: str) -> SubscriptionResponse:
        ...

    def list_for_owner(self, owner_subject: str) -> list[SubscriptionResponse]:
        ...


@dataclass(slots=True)
class _InMemorySubscriptionService:
    def purchase(self, payload: SubscriptionPurchaseRequest, owner_subject: str) -> SubscriptionResponse:
        _ = owner_subject
        return SubscriptionResponse(
            subscription_id="sub-1",
            plan_code=payload.plan_code,
            start_date=payload.start_date,
            status="pending_payment",
        )

    def list_for_owner(self, owner_subject: str) -> list[SubscriptionResponse]:
        _ = owner_subject
        return []


def get_subscription_service() -> SubscriptionService:
    return _InMemorySubscriptionService()


def _require_subject(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return str(getattr(user, "subject", ""))


@router.post("/purchase", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def purchase_subscription(
    request: Request,
    payload: SubscriptionPurchaseRequest,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    # KR-033: payment/approval/audit steps are completed in app layer.
    subject = _require_subject(request)
    return service.purchase(payload=payload, owner_subject=subject)


@router.get("", response_model=list[SubscriptionResponse])
def list_subscriptions(
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
) -> list[SubscriptionResponse]:
    subject = _require_subject(request)
    return service.list_for_owner(owner_subject=subject)
