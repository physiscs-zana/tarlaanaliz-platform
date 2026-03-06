# PATH: src/core/domain/entities/payment_intent.py
# DESC: PaymentIntent; dekont upload, manuel onay (KR-033), finansal integrity.
# SSOT: TARLAANALIZ_SSOT_v1_2_0.txt — KR-033 (odeme ve manuel onay)
"""
PaymentIntent domain entity.

Ciftci / Kooperatif / Uretici Birligi tarafindan acilan tek seferlik Mission
veya Sezonluk Paket Subscription taleplerinde tahsilati standartlastirir (KR-033).

NOT (KR-033 v1.2.0): Sistemde otomatik expire yoktur. PAYMENT_PENDING
durumundaki intent'ler admin karariyla CANCELLED yapilabilir.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class PaymentTargetType(str, Enum):
    MISSION = "MISSION"
    SUBSCRIPTION = "SUBSCRIPTION"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "CREDIT_CARD"
    IBAN_TRANSFER = "IBAN_TRANSFER"


class PaymentStatus(str, Enum):
    """KR-033 kanonik odeme durumlari (v1.2.0 — 5 durum, EXPIRED yok)."""

    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


@dataclass
class PaymentIntent:
    """Odeme niyeti domain entity'si.

    * KR-033 -- Odeme ve manuel onay akisi.
    * Kural-1: PAID olmadan Mission ASSIGNED olamaz.
    * Kural-2: PAID olmadan Subscription ACTIVE olamaz.
    * Kural-3: PAYMENT_PENDING iken kullanici veya admin CANCELLED yapabilir.
    * Kural-4: REFUNDED yalnizca PAID sonrasi admin aksiyonu ile olur.
    * Kural-5: Gecersiz gecis denemeleri PaymentTransitionError olarak reddedilir.
    """

    payment_intent_id: uuid.UUID
    payer_user_id: uuid.UUID
    target_type: PaymentTargetType
    target_id: uuid.UUID
    amount_kurus: int  # bigint, positive
    currency: str  # "TRY"
    method: PaymentMethod
    status: PaymentStatus
    payment_ref: str  # unique, e.g. PAY-20260129-4F8K2Q
    price_snapshot_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # KR-033 §4: field_id opsiyonel, IBAN eslestirme icin
    field_id: Optional[uuid.UUID] = None
    coop_id: Optional[uuid.UUID] = None
    provider: Optional[str] = None
    provider_session_id: Optional[str] = None
    provider_payment_id: Optional[str] = None
    receipt_blob_id: Optional[str] = None
    receipt_meta: Optional[Dict[str, Any]] = None
    approved_by_admin_user_id: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    # KR-033 §4: admin_note zorunlu alan (mark_paid ve reject islemlerinde)
    admin_note: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_reason: Optional[str] = None
    refunded_at: Optional[datetime] = None
    refund_amount_kurus: Optional[int] = None
    refund_reason: Optional[str] = None

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if self.amount_kurus <= 0:
            raise ValueError("amount_kurus must be positive (KR-033)")
        if self.currency != "TRY":
            raise ValueError(f"currency must be 'TRY', got '{self.currency}'")
        if not self.payment_ref or not self.payment_ref.strip():
            raise ValueError("payment_ref is required and must be unique")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Domain methods
    # ------------------------------------------------------------------
    def mark_paid(
        self,
        paid_at: Optional[datetime] = None,
        approved_by_admin_user_id: Optional[uuid.UUID] = None,
        admin_note: Optional[str] = None,
    ) -> None:
        """Odemeyi onayla (KR-033: provider webhook veya manuel admin onayi).

        PAYMENT_PENDING -> PAID.
        KR-033: PAYMENT.MARK_PAID olayinda admin_note zorunlu.
        """
        if self.status != PaymentStatus.PAYMENT_PENDING:
            raise ValueError(f"Can only mark_paid from PAYMENT_PENDING, current: {self.status.value}")
        self.status = PaymentStatus.PAID
        self.paid_at = paid_at or datetime.now(timezone.utc)
        if approved_by_admin_user_id is not None:
            self.approved_by_admin_user_id = approved_by_admin_user_id
            self.approved_at = self.paid_at
        if admin_note is not None:
            self.admin_note = admin_note.strip()
        self._touch()

    def reject(self, reason: str) -> None:
        """Odemeyi reddet (KR-033: dekont/uyumsuzluk/eksik bilgi).

        PAYMENT_PENDING -> REJECTED.
        KR-033: rejection_reason zorunlu.
        """
        if self.status != PaymentStatus.PAYMENT_PENDING:
            raise ValueError(f"Can only reject from PAYMENT_PENDING, current: {self.status.value}")
        if not reason or not reason.strip():
            raise ValueError("rejected_reason is required")
        self.status = PaymentStatus.REJECTED
        self.rejected_at = datetime.now(timezone.utc)
        self.rejected_reason = reason.strip()
        self._touch()

    def cancel(self, reason: Optional[str] = None) -> None:
        """Odeme intent'ini iptal et (KR-033 Kural-3: yalnizca PAYMENT_PENDING iken).

        PAYMENT_PENDING -> CANCELLED.
        """
        if self.status != PaymentStatus.PAYMENT_PENDING:
            raise ValueError(f"Can only cancel from PAYMENT_PENDING, current: {self.status.value} (KR-033 Kural-3)")
        self.status = PaymentStatus.CANCELLED
        self.cancelled_at = datetime.now(timezone.utc)
        self.cancelled_reason = reason.strip() if reason else None
        self._touch()

    def refund(self, refund_amount_kurus: int, reason: str) -> None:
        """Iade (KR-033 Kural-4: yalnizca PAID sonrasi admin aksiyonu).

        PAID -> REFUNDED.
        """
        if self.status != PaymentStatus.PAID:
            raise ValueError(f"Can only refund from PAID, current: {self.status.value} (KR-033 Kural-4)")
        if refund_amount_kurus <= 0:
            raise ValueError("refund_amount_kurus must be positive")
        if refund_amount_kurus > self.amount_kurus:
            raise ValueError(
                f"refund_amount_kurus ({refund_amount_kurus}) cannot exceed amount_kurus ({self.amount_kurus})"
            )
        if not reason or not reason.strip():
            raise ValueError("refund_reason is required")
        self.status = PaymentStatus.REFUNDED
        self.refunded_at = datetime.now(timezone.utc)
        self.refund_amount_kurus = refund_amount_kurus
        self.refund_reason = reason.strip()
        self._touch()

    def attach_receipt(
        self,
        receipt_blob_id: str,
        receipt_meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Dekont referansi ekle (KR-033: object store referansi, PII icermez)."""
        if not receipt_blob_id or not receipt_blob_id.strip():
            raise ValueError("receipt_blob_id is required")
        self.receipt_blob_id = receipt_blob_id
        self.receipt_meta = receipt_meta
        self._touch()
