# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-027: Sezonluk Paket Planlayıcı — subscription CRUD + pause/resume/cancel.
# KR-033: Ödeme onaylanmadan Subscription ACTIVE olamaz.
"""Subscription purchase/view/manage endpoints (KR-027)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class SubscriptionCreateRequest(BaseModel):
    """KR-027: Yeni abonelik oluşturma isteği."""

    plan_code: str = Field(min_length=2, max_length=32)
    start_date: date


class SubscriptionResponse(BaseModel):
    """KR-027: Abonelik yanıt modeli."""

    subscription_id: str
    plan_code: str
    start_date: date
    status: str


class SubscriptionService(Protocol):
    """KR-027: Subscription service port."""

    def create(self, payload: SubscriptionCreateRequest, owner_subject: str) -> SubscriptionResponse: ...

    def get_by_id(self, subscription_id: str, owner_subject: str) -> SubscriptionResponse: ...

    def list_for_owner(self, owner_subject: str) -> list[SubscriptionResponse]: ...

    def pause(self, subscription_id: str, owner_subject: str) -> SubscriptionResponse: ...

    def resume(self, subscription_id: str, owner_subject: str) -> SubscriptionResponse: ...

    def cancel(self, subscription_id: str, owner_subject: str) -> SubscriptionResponse: ...


@dataclass(slots=True)
class _InMemorySubscriptionService:
    def create(self, payload: SubscriptionCreateRequest, owner_subject: str) -> SubscriptionResponse:
        _ = owner_subject
        return SubscriptionResponse(
            subscription_id="sub-1",
            plan_code=payload.plan_code,
            start_date=payload.start_date,
            status="PENDING_PAYMENT",
        )

    def get_by_id(self, subscription_id: str, owner_subject: str) -> SubscriptionResponse:
        _ = owner_subject
        return SubscriptionResponse(
            subscription_id=subscription_id,
            plan_code="SEASONAL_COTTON",
            start_date=date(2026, 4, 1),
            status="ACTIVE",
        )

    def list_for_owner(self, owner_subject: str) -> list[SubscriptionResponse]:
        _ = owner_subject
        return []

    def pause(self, subscription_id: str, owner_subject: str) -> SubscriptionResponse:
        _ = owner_subject
        return SubscriptionResponse(
            subscription_id=subscription_id,
            plan_code="SEASONAL_COTTON",
            start_date=date(2026, 4, 1),
            status="PAUSED",
        )

    def resume(self, subscription_id: str, owner_subject: str) -> SubscriptionResponse:
        _ = owner_subject
        return SubscriptionResponse(
            subscription_id=subscription_id,
            plan_code="SEASONAL_COTTON",
            start_date=date(2026, 4, 1),
            status="ACTIVE",
        )

    def cancel(self, subscription_id: str, owner_subject: str) -> SubscriptionResponse:
        _ = owner_subject
        return SubscriptionResponse(
            subscription_id=subscription_id,
            plan_code="SEASONAL_COTTON",
            start_date=date(2026, 4, 1),
            status="CANCELLED",
        )


def get_subscription_service() -> SubscriptionService:
    return _InMemorySubscriptionService()


def _require_subject(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return str(getattr(user, "subject", ""))


# KR-027 §API: POST /subscriptions — yeni abonelik oluştur
@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    request: Request,
    payload: SubscriptionCreateRequest,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    """KR-027: Yeni Sezonluk Paket aboneliği oluştur. KR-033: PENDING_PAYMENT ile başlar."""
    subject = _require_subject(request)
    return service.create(payload=payload, owner_subject=subject)


# KR-027 §API: GET /subscriptions — kullanıcının aboneliklerini listele
@router.get("", response_model=list[SubscriptionResponse])
def list_subscriptions(
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
) -> list[SubscriptionResponse]:
    subject = _require_subject(request)
    return service.list_for_owner(owner_subject=subject)


# KR-027 §API: GET /subscriptions/{id} — detay görüntüle
@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: str,
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    """KR-027: Abonelik detayı."""
    subject = _require_subject(request)
    return service.get_by_id(subscription_id=subscription_id, owner_subject=subject)


# KR-027 §API: POST /subscriptions/{id}/pause — duraklat (PAUSED)
@router.post("/{subscription_id}/pause", response_model=SubscriptionResponse)
def pause_subscription(
    subscription_id: str,
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    """KR-027: Aboneliği duraklat."""
    subject = _require_subject(request)
    return service.pause(subscription_id=subscription_id, owner_subject=subject)


# KR-027 §API: POST /subscriptions/{id}/resume — devam ettir (ACTIVE)
@router.post("/{subscription_id}/resume", response_model=SubscriptionResponse)
def resume_subscription(
    subscription_id: str,
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    """KR-027: Aboneliği devam ettir."""
    subject = _require_subject(request)
    return service.resume(subscription_id=subscription_id, owner_subject=subject)


# KR-027 §API: POST /subscriptions/{id}/cancel — iptal et (CANCELLED)
@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: str,
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    """KR-027: Aboneliği iptal et."""
    subject = _require_subject(request)
    return service.cancel(subscription_id=subscription_id, owner_subject=subject)
