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
        target_type=PaymentTargetType.SUBSCRIPTION,
        target_id=uuid.uuid4(),
        amount_kurus=50_000,
        currency="TRY",
        method=PaymentMethod.IBAN_TRANSFER,
        status=PaymentStatus.PAYMENT_PENDING,
        payment_ref="PAY-20260101-BBBB2222",
        price_snapshot_id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )


def test_kr033_manual_approval_moves_status_to_paid_and_sets_admin() -> None:
    intent = _intent()
    admin_id = uuid.uuid4()

    intent.mark_paid(approved_by_admin_user_id=admin_id, admin_note="Manual payment approval")

    assert intent.status == PaymentStatus.PAID
    assert intent.approved_by_admin_user_id == admin_id


def test_kr033_approval_not_allowed_from_rejected() -> None:
    intent = _intent()
    intent.reject("invalid receipt")

    with pytest.raises(ValueError, match="PAYMENT_PENDING"):
        intent.mark_paid(approved_by_admin_user_id=uuid.uuid4(), admin_note="Test approval")
