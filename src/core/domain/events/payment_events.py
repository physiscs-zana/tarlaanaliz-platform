# PATH: src/core/domain/events/payment_events.py
# DESC: Payment domain event'leri (PaymentIntentCreated, ReceiptUploaded, PaymentApproved, PaymentRejected).

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from src.core.domain.events.base import DomainEvent


@dataclass(frozen=True)
class PaymentIntentCreated(DomainEvent):
    """Ödeme niyeti oluşturuldu (KR-033).

    PaymentIntent olmadan paid state olmaz.
    Fiyat snapshot sipariş anında alınır (immutability).
    """

    payment_intent_id: uuid.UUID = field(default_factory=uuid.uuid4)
    subscription_id: uuid.UUID | None = None
    amount_kurus: int = 0  # Kuruş cinsinden tutar
    currency: str = "TRY"

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "payment_intent_id": str(self.payment_intent_id),
                "subscription_id": str(self.subscription_id) if self.subscription_id else None,
                "amount_kurus": self.amount_kurus,
                "currency": self.currency,
            }
        )
        return base


@dataclass(frozen=True)
class ReceiptUploaded(DomainEvent):
    """Dekont yüklendi (KR-033: dekont + manuel onay + audit)."""

    payment_intent_id: uuid.UUID = field(default_factory=uuid.uuid4)
    receipt_blob_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "payment_intent_id": str(self.payment_intent_id),
                "receipt_blob_id": self.receipt_blob_id,
            }
        )
        return base


@dataclass(frozen=True)
class PaymentApproved(DomainEvent):
    """Ödeme onaylandı (admin manuel onayı, KR-033).

    Audit zorunlu: kim, ne zaman, hangi ödeme.
    """

    payment_intent_id: uuid.UUID = field(default_factory=uuid.uuid4)
    approved_by: uuid.UUID = field(default_factory=uuid.uuid4)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "payment_intent_id": str(self.payment_intent_id),
                "approved_by": str(self.approved_by),
            }
        )
        return base


@dataclass(frozen=True)
class PaymentRejected(DomainEvent):
    """Ödeme reddedildi (KR-033)."""

    payment_intent_id: uuid.UUID = field(default_factory=uuid.uuid4)
    rejected_by: uuid.UUID = field(default_factory=uuid.uuid4)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "payment_intent_id": str(self.payment_intent_id),
                "rejected_by": str(self.rejected_by),
                "reason": self.reason,
            }
        )
        return base
