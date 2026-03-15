# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033: Payment DTO definitions for manual approval flow.
"""DTOs for payment application use-cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.core.domain.entities.payment_intent import PaymentMethod, PaymentTargetType


@dataclass(frozen=True, slots=True)
class CreatePaymentIntentInput:
    """Input DTO for creating a payment intent."""

    payer_user_id: str
    target_type: PaymentTargetType
    target_id: str
    amount_kurus: int
    currency: str
    method: PaymentMethod
    price_snapshot_id: str
    provider: str | None = None


@dataclass(frozen=True, slots=True)
class UploadReceiptInput:
    """Input DTO for attaching receipt proof."""

    payment_intent_id: str
    receipt_blob_id: str
    receipt_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ApprovePaymentInput:
    """Input DTO for manual payment approval."""

    payment_intent_id: str
    approved_by_admin_user_id: str
    admin_note: str = ""


@dataclass(frozen=True, slots=True)
class RejectPaymentInput:
    """Input DTO for payment rejection."""

    payment_intent_id: str
    reason: str
    rejected_by_admin_user_id: str


@dataclass(frozen=True, slots=True)
class PaymentOperationResult:
    """Output DTO for payment operations."""

    payment_intent_id: str
    status: str
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "payment_intent_id": self.payment_intent_id,
            "status": self.status,
            "updated_at": _to_utc_iso(self.updated_at),
        }


def _to_utc_iso(value: datetime) -> str:
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
