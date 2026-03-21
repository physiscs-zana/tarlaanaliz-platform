# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# PATH: src/presentation/api/v1/schemas/payment_webhook_schemas.py
# DESC: Payment webhook payload validation schema (KR-033).

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class PaymentStatus(str, Enum):
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class WebhookEventType(str, Enum):
    payment_intent_created = "payment_intent.created"
    payment_intent_succeeded = "payment_intent.succeeded"
    payment_intent_failed = "payment_intent.failed"
    refund_created = "refund.created"


# ---------------------------------------------------------------------------
# Request schemas (webhook payloads)
# ---------------------------------------------------------------------------

class PaymentWebhookPayload(SchemaBase):
    # KR-033: webhook payload from payment provider.
    event_id: str = Field(min_length=3, max_length=128)
    event_type: WebhookEventType
    provider_ref: str = Field(min_length=2, max_length=128)
    status: PaymentStatus
    payment_intent_id: str = Field(min_length=3, max_length=128)
    amount_kurus: Optional[int] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    occurred_at: Optional[datetime] = None
    idempotency_key: Optional[str] = Field(default=None, min_length=3, max_length=128)
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class WebhookAckResponse(SchemaBase):
    received: bool
    deduplicated: bool
    event_id: str = Field(min_length=3, max_length=128)
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)
