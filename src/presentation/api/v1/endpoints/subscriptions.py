# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-027: Sezonluk Paket Planlayıcı — subscription CRUD + pause/resume/cancel.
# KR-033: Ödeme onaylanmadan Subscription ACTIVE olamaz.
"""Subscription purchase/view/manage endpoints (KR-027)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Protocol, cast
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel
from src.infrastructure.persistence.sqlalchemy.models.payment_intent_model import PaymentIntentModel
from src.infrastructure.persistence.sqlalchemy.models.price_snapshot_model import PriceSnapshotModel
from src.infrastructure.persistence.sqlalchemy.models.subscription_model import SubscriptionModel
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

logger = logging.getLogger("api.subscriptions")

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class SubscriptionCreateRequest(BaseModel):
    """KR-027: Yeni abonelik oluşturma isteği."""

    field_id: str = Field(min_length=3, max_length=64)
    crop_type: str = Field(min_length=2, max_length=50)
    start_date: date
    end_date: date
    interval_days: int = Field(ge=1, le=30)
    plan_code: str = Field(default="SEASONAL", min_length=2, max_length=32)


class SubscriptionResponse(BaseModel):
    """KR-027: Abonelik yanıt modeli."""

    subscription_id: str
    plan_code: str
    start_date: date
    status: str
    field_id: str | None = None
    crop_type: str | None = None
    end_date: date | None = None
    interval_days: int | None = None
    payment_intent_id: str | None = None
    amount_kurus: int | None = None


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
            field_id=payload.field_id,
            crop_type=payload.crop_type,
            end_date=payload.end_date,
            interval_days=payload.interval_days,
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


def get_subscription_service(request: Request) -> SubscriptionService:
    services = getattr(request.app.state, "services", None)
    if services is not None:
        svc = services.get("subscription_service")
        if svc is not None:
            return cast(SubscriptionService, svc)
    return _InMemorySubscriptionService()


def _require_subject(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return str(getattr(user, "subject", ""))


def _require_user_id(request: Request) -> uuid.UUID:
    """Extract user_id (UUID) from request.state.user. Raises 401 if missing."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    user_id = getattr(user, "user_id", None) or getattr(user, "subject", None)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized — user_id missing")
    try:
        return uuid.UUID(str(user_id))
    except ValueError as exc:
        logger.warning("INVALID_USER_ID: could not parse user_id=%s", user_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized — invalid user_id") from exc


def _calculate_price_inline(crop_type: str, area_m2: Decimal, total_scans: int) -> int:
    """Inline pricing fallback when pricing_service is unavailable.

    Returns amount in kuruş (TRY cents).
    Formula: seasonal_price (TL) * 100 (kuruş) * area_ha * total_scans
    """
    from src.presentation.api.v1.endpoints.admin_pricing import _read_config

    config = _read_config()
    crops = config.get("crops", [])
    seasonal_price: int | float = 120  # default fallback
    if isinstance(crops, list):
        for crop in crops:
            if isinstance(crop, dict) and crop.get("code") == crop_type:
                seasonal_price = crop.get("seasonal_price", 120)  # type: ignore[assignment]
                break

    area_ha = float(area_m2) / 10_000.0
    amount_kurus = int(float(seasonal_price) * 100 * area_ha * total_scans)
    return max(amount_kurus, 100)  # minimum 1 TL


# KR-027 §API: POST /subscriptions — yeni abonelik oluştur
@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request: Request,
    payload: SubscriptionCreateRequest,
) -> SubscriptionResponse:
    """KR-027: Yeni Sezonluk Paket aboneliği oluştur. KR-033: PENDING_PAYMENT ile başlar."""

    # --- 1. Authenticate ---
    user_id = _require_user_id(request)

    # --- 2. Validate field_id as UUID ---
    try:
        field_uuid = uuid.UUID(payload.field_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"field_id is not a valid UUID: {payload.field_id}",
        ) from exc

    # --- 3. Validate date range ---
    if payload.end_date <= payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be after start_date",
        )

    # --- 4. Calculate total scans ---
    total_scans = max(1, (payload.end_date - payload.start_date).days // payload.interval_days)

    async with get_async_session() as session:
        # --- 5. Look up the field to get area_m2 and verify existence ---
        field_result = await session.execute(select(FieldModel).where(FieldModel.field_id == field_uuid))
        field_row: FieldModel | None = field_result.scalars().first()
        if field_row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Field not found: {payload.field_id}",
            )

        area_m2: Decimal = field_row.area_m2

        # --- 6. Calculate price ---
        try:
            from src.application.services.pricing_service import calculate_subscription_price

            amount_kurus: int = calculate_subscription_price(
                field_id=field_uuid,
                crop_type=payload.crop_type,
                area_m2=area_m2,
                total_scans=total_scans,
            )
        except (ImportError, ModuleNotFoundError):
            logger.warning(
                "PRICING_SERVICE_UNAVAILABLE: falling back to inline calculation for field_id=%s crop=%s",
                field_uuid,
                payload.crop_type,
            )
            amount_kurus = _calculate_price_inline(payload.crop_type, area_m2, total_scans)

        # --- 7. Create a price snapshot for this subscription ---
        now = datetime.now(timezone.utc)
        snapshot_id = uuid4()
        price_snapshot = PriceSnapshotModel(
            price_snapshot_id=snapshot_id,
            crop_type=payload.crop_type,
            analysis_type="SEASONAL",
            unit_price_kurus=amount_kurus,
            currency="TRY",
            effective_from=now,
        )
        session.add(price_snapshot)
        await session.flush()  # ensure snapshot_id is available for FK

        # --- 8. Create SubscriptionModel ---
        subscription_id = uuid4()
        subscription = SubscriptionModel(
            subscription_id=subscription_id,
            farmer_user_id=user_id,
            field_id=field_uuid,
            price_snapshot_id=snapshot_id,
            crop_type=payload.crop_type,
            analysis_type="SEASONAL",
            interval_days=payload.interval_days,
            start_date=payload.start_date,
            end_date=payload.end_date,
            next_due_at=datetime.combine(payload.start_date, datetime.min.time()).replace(tzinfo=timezone.utc),
            status="PENDING_PAYMENT",
            reschedule_tokens_remaining=2,
            plan_type=payload.plan_code,
            reschedule_tokens_per_season=2,
        )
        session.add(subscription)
        await session.flush()

        # --- 9. Create PaymentIntentModel ---
        payment_intent_id = uuid4()
        payment_ref = f"PAY-{now:%Y%m%d}-{uuid4().hex[:6].upper()}"
        payment_intent = PaymentIntentModel(
            payment_intent_id=payment_intent_id,
            payer_user_id=user_id,
            target_type="SUBSCRIPTION",
            target_id=subscription_id,
            amount_kurus=amount_kurus,
            currency="TRY",
            method="IBAN_TRANSFER",
            status="PAYMENT_PENDING",
            payment_ref=payment_ref,
            price_snapshot_id=snapshot_id,
        )
        session.add(payment_intent)

        # --- 10. Link payment_intent back to subscription ---
        subscription.payment_intent_id = payment_intent_id

        await session.commit()

        logger.warning(
            "SUBSCRIPTION_CREATED: subscription_id=%s user_id=%s field_id=%s amount_kurus=%d scans=%d payment_ref=%s",
            subscription_id,
            user_id,
            field_uuid,
            amount_kurus,
            total_scans,
            payment_ref,
        )

        return SubscriptionResponse(
            subscription_id=str(subscription_id),
            plan_code=payload.plan_code,
            start_date=payload.start_date,
            status="PENDING_PAYMENT",
            field_id=str(field_uuid),
            crop_type=payload.crop_type,
            end_date=payload.end_date,
            interval_days=payload.interval_days,
            payment_intent_id=str(payment_intent_id),
            amount_kurus=amount_kurus,
        )


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
