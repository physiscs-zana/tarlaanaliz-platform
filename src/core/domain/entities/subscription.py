# PATH: src/core/domain/entities/subscription.py
# DESC: Subscription; fiyat snapshot (KR-022), reschedule token (KR-015-5).
# SSOT: KR-027 (abonelik planlayici), KR-015-5 (tarama takvimi), KR-033 (odeme)
"""
Subscription domain entity.

Sezonluk Paket secen kullanicilar icin otomatik, periyodik Mission uretimi.
PAID olmadan Subscription ACTIVE olamaz (KR-033 Kural-2).
Sezonda sinirli gun degistirme hakki: varsayilan 2 token (KR-015-5).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Optional


class SubscriptionStatus(str, Enum):
    """KR-027 kanonik abonelik durumlari."""

    PENDING_PAYMENT = "PENDING_PAYMENT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class SubscriptionPlanType(str, Enum):
    """KR-027 abonelik plan turu (KR-015-5: sezonluk tarama takvimi)."""

    SEASONAL = "SEASONAL"


@dataclass
class Subscription:
    """Abonelik domain entity'si.

    * KR-027   -- Abonelik planlayici (scheduler) ve veri modeli.
    * KR-015-5 -- Sezonluk abonelikte tarama takvimi ve reschedule token.
    * KR-033   -- PAID olmadan ACTIVE olamaz; PENDING_PAYMENT'da scheduler Mission uretmez.
    """

    subscription_id: uuid.UUID
    farmer_user_id: uuid.UUID
    field_id: uuid.UUID
    crop_type: str
    analysis_type: str
    interval_days: int
    start_date: date
    end_date: date
    next_due_at: datetime
    status: SubscriptionStatus
    price_snapshot_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    payment_intent_id: Optional[uuid.UUID] = None
    plan_type: SubscriptionPlanType = SubscriptionPlanType.SEASONAL
    reschedule_tokens_per_season: int = 2
    reschedule_tokens_used: int = 0

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if not self.crop_type:
            raise ValueError("crop_type is required")
        if not self.analysis_type:
            raise ValueError("analysis_type is required")
        if self.interval_days <= 0:
            raise ValueError("interval_days must be > 0 (KR-027)")
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------
    @property
    def is_due(self) -> bool:
        """Scheduler tarafindan kontrol: status=ACTIVE ve next_due_at <= now (KR-027)."""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        return self.next_due_at <= datetime.now(timezone.utc)

    @property
    def remaining_reschedule_tokens(self) -> int:
        return max(0, self.reschedule_tokens_per_season - self.reschedule_tokens_used)

    # ------------------------------------------------------------------
    # Domain methods
    # ------------------------------------------------------------------
    def activate(self) -> None:
        """Aboneligi aktif et (KR-033 Kural-2: yalnizca PENDING_PAYMENT'dan).

        Caller, PaymentIntent.status == PAID kontrolunu yapmalidir.
        """
        if self.status != SubscriptionStatus.PENDING_PAYMENT:
            raise ValueError(f"Can only activate from PENDING_PAYMENT, current: {self.status.value} (KR-033 Kural-2)")
        self.status = SubscriptionStatus.ACTIVE
        self._touch()

    def pause(self) -> None:
        """Aboneligi duraklat (ACTIVE -> PAUSED)."""
        if self.status != SubscriptionStatus.ACTIVE:
            raise ValueError(f"Can only pause from ACTIVE, current: {self.status.value}")
        self.status = SubscriptionStatus.PAUSED
        self._touch()

    def resume(self) -> None:
        """Aboneligi devam ettir (PAUSED -> ACTIVE)."""
        if self.status != SubscriptionStatus.PAUSED:
            raise ValueError(f"Can only resume from PAUSED, current: {self.status.value}")
        self.status = SubscriptionStatus.ACTIVE
        self._touch()

    def cancel(self) -> None:
        """Aboneligi iptal et (herhangi aktif/paused -> CANCELLED)."""
        if self.status == SubscriptionStatus.CANCELLED:
            raise ValueError("Subscription is already cancelled")
        self.status = SubscriptionStatus.CANCELLED
        self._touch()

    def advance_due_date(self) -> None:
        """next_due_at'i interval_days kadar ileri tasir (KR-027 scheduler kurali)."""
        if self.status != SubscriptionStatus.ACTIVE:
            raise ValueError(f"Can only advance due date when ACTIVE, current: {self.status.value}")
        self.next_due_at = self.next_due_at + timedelta(days=self.interval_days)
        self._touch()

    def consume_reschedule_token(self) -> None:
        """Sezonda sinirli gun degistirme hakki kullan (KR-015-5).

        Hava engeli (Weather Block) / force majeure nedeniyle yapilanlar
        token TUKETMEZ; bu kontrol caller sorumlulugundadir.
        """
        if self.reschedule_tokens_used >= self.reschedule_tokens_per_season:
            raise ValueError(
                f"No reschedule tokens remaining "
                f"({self.reschedule_tokens_used}/{self.reschedule_tokens_per_season}) "
                f"(KR-015-5)"
            )
        self.reschedule_tokens_used += 1
        self._touch()
