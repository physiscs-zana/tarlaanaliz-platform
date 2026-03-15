# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Test modülü; davranış doğrulama ve regresyon engeli.
Sorumluluk: Bağlamına göre beklenen sorumlulukları yerine getirir; SSOT v1.0.0 ile uyumlu kalır.
Girdi/Çıktı (Contract/DTO/Event): N/A
Güvenlik (RBAC/PII/Audit): N/A
Hata Modları (idempotency/retry/rate limit): N/A
Observability (log fields/metrics/traces): N/A
Testler: N/A
Bağımlılıklar: N/A
Notlar/SSOT: Tek referans: SSOT v1.0.0. Aynı kavram başka yerde tekrar edilmez. KR-033: PaymentIntent olmadan paid state olmaz; dekont + manuel onay + audit.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from src.core.domain.entities.payment_intent import (
    PaymentIntent,
    PaymentMethod,
    PaymentStatus,
    PaymentTargetType,
)


def _intent() -> PaymentIntent:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return PaymentIntent(
        payment_intent_id=uuid.uuid4(),
        payer_user_id=uuid.uuid4(),
        target_type=PaymentTargetType.MISSION,
        target_id=uuid.uuid4(),
        amount_kurus=100_000,
        currency="TRY",
        method=PaymentMethod.IBAN_TRANSFER,
        status=PaymentStatus.PAYMENT_PENDING,
        payment_ref="PAY-20260101-AAAA1111",
        price_snapshot_id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )


def test_kr033_mark_paid_only_from_pending() -> None:
    intent = _intent()
    intent.mark_paid(approved_by_admin_user_id=uuid.uuid4(), admin_note="Test approval")

    assert intent.status == PaymentStatus.PAID

    with pytest.raises(ValueError, match="PAYMENT_PENDING"):
        intent.mark_paid()


def test_kr033_attach_receipt_updates_proof_reference() -> None:
    intent = _intent()
    intent.attach_receipt(receipt_blob_id="blob://receipt-1")

    assert intent.receipt_blob_id == "blob://receipt-1"

    intent.mark_paid(approved_by_admin_user_id=uuid.uuid4(), admin_note="Test approval")
    intent.attach_receipt(receipt_blob_id="blob://receipt-2")

    assert intent.receipt_blob_id == "blob://receipt-2"


def test_refund_requires_paid_status() -> None:
    intent = _intent()

    with pytest.raises(ValueError, match="Can only refund from PAID"):
        intent.refund(10_000, reason="ops")
