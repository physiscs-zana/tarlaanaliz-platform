# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033: Webhook integrity; provider signature HMAC verification.
"""Payment provider webhook receiver."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from dataclasses import dataclass, field
from typing import Protocol

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

LOGGER = logging.getLogger("api.payment_webhooks")

router = APIRouter(prefix="/payments/webhooks", tags=["payment-webhooks"])


class PaymentWebhookPayload(BaseModel):
    provider_event_id: str = Field(min_length=3, max_length=128)
    payment_intent_id: str = Field(min_length=3, max_length=64)
    event_type: str = Field(min_length=3, max_length=64)
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)


class PaymentWebhookResponse(BaseModel):
    accepted: bool
    provider_event_id: str


class PaymentWebhookService(Protocol):
    def process(
        self, payload: PaymentWebhookPayload, signature: str | None, raw_body: bytes | None = None
    ) -> PaymentWebhookResponse: ...


@dataclass(slots=True)
class _InMemoryPaymentWebhookService:
    processed_events: set[str] = field(default_factory=set)

    def process(
        self, payload: PaymentWebhookPayload, signature: str | None, raw_body: bytes | None = None
    ) -> PaymentWebhookResponse:
        if not signature:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        # HMAC signature verification (KR-033: webhook integrity)
        # SEC-FIX: webhook_secret boşsa HMAC doğrulama atlanamaz — servis hazır değil
        webhook_secret = os.getenv("PAYMENT_WEBHOOK_SECRET", "")
        if not webhook_secret:
            LOGGER.error("PAYMENT_WEBHOOK_SECRET not configured — rejecting webhook")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Webhook verification not configured",
            )
        if raw_body:
            expected = hmac.new(
                webhook_secret.encode("utf-8"),
                raw_body,
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected, signature):
                LOGGER.warning("Webhook signature mismatch", extra={"event": "webhook_sig_fail"})
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

        if payload.provider_event_id in self.processed_events:
            return PaymentWebhookResponse(accepted=True, provider_event_id=payload.provider_event_id)

        # KR-033: webhook cannot finalize paid state without PaymentIntent + manual approval in app layer.
        self.processed_events.add(payload.provider_event_id)
        return PaymentWebhookResponse(accepted=True, provider_event_id=payload.provider_event_id)


_WEBHOOK_SERVICE = _InMemoryPaymentWebhookService()


def get_payment_webhook_service() -> PaymentWebhookService:
    return _WEBHOOK_SERVICE


@router.post("/provider", response_model=PaymentWebhookResponse)
async def receive_provider_webhook(
    request: Request,
    payload: PaymentWebhookPayload,
    x_provider_signature: str | None = Header(default=None, alias="X-Provider-Signature"),
    service: PaymentWebhookService = Depends(get_payment_webhook_service),
) -> PaymentWebhookResponse:
    raw_body = await request.body()
    result = service.process(payload=payload, signature=x_provider_signature, raw_body=raw_body)
    # KR-033 §8: PAYMENT.WEBHOOK_PAID — update intent to PAID + auto-dispatch pilot
    if result.accepted and payload.event_type in ("payment.success", "payment.completed", "PAID"):
        corr_id = getattr(request.state, "corr_id", None)
        LOGGER.warning(
            "PAYMENT.WEBHOOK_PAID intent=%s event=%s",
            payload.payment_intent_id,
            payload.event_type,
        )
        try:
            import uuid as _uuid
            from datetime import datetime, timezone

            from sqlalchemy import select as sa_select
            from sqlalchemy.orm import selectinload

            from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel
            from src.infrastructure.persistence.sqlalchemy.models.mission_model import MissionModel
            from src.infrastructure.persistence.sqlalchemy.models.payment_intent_model import PaymentIntentModel
            from src.infrastructure.persistence.sqlalchemy.models.pilot_model import (
                MissionAssignmentModel,
                PilotModel,
                PilotServiceAreaModel,
            )
            from src.infrastructure.persistence.sqlalchemy.session import get_async_session

            async with get_async_session() as session:
                # Find and update payment intent
                intent_result = await session.execute(
                    sa_select(PaymentIntentModel).where(
                        PaymentIntentModel.payment_intent_id == _uuid.UUID(payload.payment_intent_id)
                    )
                )
                intent = intent_result.scalar_one_or_none()
                if intent and intent.status != "PAID":
                    now = datetime.now(timezone.utc)
                    intent.status = "PAID"
                    intent.paid_at = now
                    intent.updated_at = now

                    # Auto-dispatch pilot for linked mission
                    if intent.target_type == "MISSION" and intent.target_id:
                        mission_result = await session.execute(
                            sa_select(MissionModel).where(MissionModel.mission_id == intent.target_id)
                        )
                        mission = mission_result.scalar_one_or_none()

                        if mission and mission.status == "PLANNED":
                            field_province = None
                            field_area_donum = 0
                            field_result = await session.execute(
                                sa_select(FieldModel.province, FieldModel.area_donum).where(
                                    FieldModel.field_id == mission.field_id
                                )
                            )
                            field_row = field_result.one_or_none()
                            if field_row:
                                field_province = field_row.province
                                field_area_donum = int(field_row.area_donum)

                            assigned_pilot_id = None
                            if field_province:
                                pilot_stmt = (
                                    sa_select(PilotModel)
                                    .join(
                                        PilotServiceAreaModel,
                                        PilotModel.pilot_id == PilotServiceAreaModel.pilot_id,
                                    )
                                    .where(PilotModel.is_active.is_(True))
                                    .where(PilotServiceAreaModel.province == field_province)
                                    .order_by(PilotModel.reliability_score.desc())
                                )
                                pilot_result = await session.execute(pilot_stmt)
                                eligible_pilots = pilot_result.scalars().unique().all()

                                for pilot in eligible_pilots:
                                    if pilot.daily_capacity_donum >= field_area_donum:
                                        assigned_pilot_id = pilot.pilot_id
                                        session.add(
                                            MissionAssignmentModel(
                                                mission_id=intent.target_id,
                                                pilot_id=pilot.pilot_id,
                                                assignment_type="SYSTEM_SEED",
                                                is_current=True,
                                            )
                                        )
                                        break

                            mission.status = "ASSIGNED"
                            LOGGER.warning(
                                "WEBHOOK.AUTO_DISPATCHED mission=%s pilot=%s province=%s",
                                intent.target_id,
                                assigned_pilot_id,
                                field_province,
                            )

                    await session.commit()
        except Exception as exc:
            LOGGER.error("WEBHOOK.DISPATCH_FAILED intent=%s error=%s", payload.payment_intent_id, exc)

    return result
