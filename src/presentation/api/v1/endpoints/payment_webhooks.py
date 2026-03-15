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
    # KR-033 §8: PAYMENT.WEBHOOK_PAID audit event
    if result.accepted:
        corr_id = getattr(request.state, "corr_id", None)
        LOGGER.info(
            "PAYMENT.WEBHOOK_PAID",
            extra={
                "event": "PAYMENT.WEBHOOK_PAID",
                "provider_event_id": payload.provider_event_id,
                "payment_intent_id": payload.payment_intent_id,
                "corr_id": corr_id,
            },
        )
    return result
