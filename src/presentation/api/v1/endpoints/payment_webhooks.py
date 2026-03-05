# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Payment provider webhook receiver."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

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
    def process(self, payload: PaymentWebhookPayload, signature: str | None) -> PaymentWebhookResponse:
        ...


@dataclass(slots=True)
class _InMemoryPaymentWebhookService:
    processed_events: set[str] = field(default_factory=set)

    def process(self, payload: PaymentWebhookPayload, signature: str | None) -> PaymentWebhookResponse:
        if not signature:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        if payload.provider_event_id in self.processed_events:
            return PaymentWebhookResponse(accepted=True, provider_event_id=payload.provider_event_id)

        # KR-033: webhook cannot finalize paid state without PaymentIntent + manual approval in app layer.
        self.processed_events.add(payload.provider_event_id)
        return PaymentWebhookResponse(accepted=True, provider_event_id=payload.provider_event_id)


_WEBHOOK_SERVICE = _InMemoryPaymentWebhookService()


def get_payment_webhook_service() -> PaymentWebhookService:
    return _WEBHOOK_SERVICE


@router.post("/provider", response_model=PaymentWebhookResponse)
def receive_provider_webhook(
    request: Request,
    payload: PaymentWebhookPayload,
    x_provider_signature: str | None = Header(default=None, alias="X-Provider-Signature"),
    service: PaymentWebhookService = Depends(get_payment_webhook_service),
) -> PaymentWebhookResponse:
    _ = request
    return service.process(payload=payload, signature=x_provider_signature)
