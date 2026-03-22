# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Test modülü; davranış doğrulama ve regresyon engeli.
Sorumluluk: Subscription domain entity; KR-027/KR-015-5/KR-033 uyumu.
Girdi/Çıktı (Contract/DTO/Event): N/A
Güvenlik (RBAC/PII/Audit): N/A
Hata Modları (idempotency/retry/rate limit): N/A
Observability (log fields/metrics/traces): N/A
Testler: N/A
Bağımlılıklar: N/A
Notlar/SSOT: Tek referans: SSOT v1.0.0. Aynı kavram başka yerde tekrar edilmez.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from src.core.domain.entities.subscription import (
    Subscription,
    SubscriptionPlanType,
    SubscriptionStatus,
)


def _subscription(**overrides) -> Subscription:
    now = datetime.now(timezone.utc)
    defaults = dict(
        subscription_id=uuid.uuid4(),
        farmer_user_id=uuid.uuid4(),
        field_id=uuid.uuid4(),
        crop_type="WHEAT",
        analysis_type="MULTISPECTRAL",
        interval_days=14,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        next_due_at=now + timedelta(days=14),
        status=SubscriptionStatus.PENDING_PAYMENT,
        price_snapshot_id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return Subscription(**defaults)


def test_subscription_default_plan_type_is_seasonal() -> None:
    """plan_type varsayılanı SubscriptionPlanType.SEASONAL olmalı (KR-027)."""
    sub = _subscription()
    assert sub.plan_type == SubscriptionPlanType.SEASONAL


def test_subscription_activate_requires_pending_payment() -> None:
    """activate() yalnızca PENDING_PAYMENT'dan çalışmalı (KR-033 Kural-2)."""
    sub = _subscription(status=SubscriptionStatus.PENDING_PAYMENT)
    sub.activate()
    assert sub.status == SubscriptionStatus.ACTIVE


def test_subscription_activate_from_active_raises() -> None:
    """Zaten ACTIVE olan aboneliği aktif etmek ValueError vermeli (KR-033)."""
    sub = _subscription(status=SubscriptionStatus.ACTIVE)
    with pytest.raises(ValueError, match="PENDING_PAYMENT"):
        sub.activate()


def test_subscription_reschedule_token_consumption() -> None:
    """consume_reschedule_token() token bitince ValueError vermeli (KR-015-5)."""
    sub = _subscription(
        status=SubscriptionStatus.ACTIVE,
        reschedule_tokens_per_season=2,
        reschedule_tokens_used=0,
    )
    sub.consume_reschedule_token()
    sub.consume_reschedule_token()
    assert sub.remaining_reschedule_tokens == 0

    with pytest.raises(ValueError, match="KR-015-5"):
        sub.consume_reschedule_token()


def test_subscription_advance_due_date() -> None:
    """advance_due_date() next_due_at'i interval_days kadar ilerletmeli (KR-027)."""
    now = datetime.now(timezone.utc)
    sub = _subscription(
        status=SubscriptionStatus.ACTIVE,
        interval_days=14,
        next_due_at=now,
    )
    sub.advance_due_date()
    assert sub.next_due_at == now + timedelta(days=14)


def test_subscription_remaining_tokens_computed() -> None:
    """remaining_reschedule_tokens = per_season - used (KR-015-5)."""
    sub = _subscription(reschedule_tokens_per_season=3, reschedule_tokens_used=1)
    assert sub.remaining_reschedule_tokens == 2
