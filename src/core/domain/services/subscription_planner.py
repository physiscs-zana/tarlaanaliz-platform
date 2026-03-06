# PATH: src/core/domain/services/subscription_planner.py
# DESC: Sezonluk paket takvim hesaplama ve reschedule token (KR-015-5).

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum


class SubscriptionPlanningError(Exception):
    """Subscription planlama domain invariant ihlali."""


class RescheduleType(Enum):
    """Yeniden planlama türü."""

    FARMER_REQUEST = "farmer_request"  # Çiftçi talebi (token tüketir)
    SYSTEM_RESCHEDULE = "system_reschedule"  # Sistem kaynaklı
    WEATHER_BLOCK = "weather_block"  # Hava koşulları (token tüketmez, force majeure)


@dataclass(frozen=True)
class SubscriptionConfig:
    """Abonelik yapılandırması."""

    subscription_id: uuid.UUID
    field_id: uuid.UUID
    crop_type: str
    start_date: date
    end_date: date
    interval_days: int  # Analizler arası gün sayısı
    total_analyses: int
    reschedule_tokens: int  # Kullanılabilir yeniden planlama hakkı


@dataclass(frozen=True)
class ScheduledAnalysis:
    """Planlı analiz."""

    sequence_number: int  # 1-based sıra numarası
    scheduled_date: date
    mission_id: uuid.UUID | None = None  # Atanmışsa


@dataclass(frozen=True)
class SubscriptionSchedule:
    """Abonelik takvimi."""

    subscription_id: uuid.UUID
    analyses: tuple[ScheduledAnalysis, ...]
    remaining_reschedule_tokens: int


@dataclass(frozen=True)
class RescheduleResult:
    """Yeniden planlama sonucu."""

    subscription_id: uuid.UUID
    mission_id: uuid.UUID
    old_date: date
    new_date: date
    reschedule_type: RescheduleType
    token_consumed: bool
    remaining_tokens: int
    success: bool
    reason: str


class SubscriptionPlanner:
    """Sezonluk paket takvim hesaplama ve reschedule token servisi (KR-015-5).

    Tek entity'ye sığmayan saf iş mantığı; policy ve hesaplamalar.

    Domain invariants:
    - Analiz tarihleri abonelik dönemi içinde olmalıdır.
    - Analizler arası minimum interval_days gün olmalıdır.
    - Çiftçi yeniden planlaması reschedule token tüketir.
    - Weather block (force majeure) token tüketmez.
    - Token yoksa çiftçi yeniden planlama yapamaz.
    - total_analyses kadar analiz planlanmalıdır.
    """

    def generate_schedule(
        self,
        config: SubscriptionConfig,
    ) -> SubscriptionSchedule:
        """Abonelik takvimi oluşturur.

        Analizleri start_date'den başlayarak interval_days aralıklarla planlar.

        Args:
            config: Abonelik yapılandırması.

        Returns:
            SubscriptionSchedule: Oluşturulan takvim.

        Raises:
            SubscriptionPlanningError: Geçersiz yapılandırma.
        """
        self._validate_config(config)

        analyses: list[ScheduledAnalysis] = []
        current_date = config.start_date

        for seq in range(1, config.total_analyses + 1):
            if current_date > config.end_date:
                break

            analyses.append(
                ScheduledAnalysis(
                    sequence_number=seq,
                    scheduled_date=current_date,
                )
            )
            current_date += timedelta(days=config.interval_days)

        return SubscriptionSchedule(
            subscription_id=config.subscription_id,
            analyses=tuple(analyses),
            remaining_reschedule_tokens=config.reschedule_tokens,
        )

    def reschedule_analysis(
        self,
        *,
        schedule: SubscriptionSchedule,
        mission_id: uuid.UUID,
        old_date: date,
        new_date: date,
        reschedule_type: RescheduleType,
        subscription_end_date: date,
    ) -> RescheduleResult:
        """Analizi yeniden planlar.

        Args:
            schedule: Mevcut takvim.
            mission_id: Mission ID.
            old_date: Eski tarih.
            new_date: Yeni tarih.
            reschedule_type: Yeniden planlama türü.
            subscription_end_date: Abonelik bitiş tarihi.

        Returns:
            RescheduleResult: Yeniden planlama sonucu.
        """
        # Tarih doğrulaması
        if new_date > subscription_end_date:
            return RescheduleResult(
                subscription_id=schedule.subscription_id,
                mission_id=mission_id,
                old_date=old_date,
                new_date=new_date,
                reschedule_type=reschedule_type,
                token_consumed=False,
                remaining_tokens=schedule.remaining_reschedule_tokens,
                success=False,
                reason="Yeni tarih abonelik bitiş tarihini aşıyor.",
            )

        # Token kontrolü (weather block hariç)
        token_consumed = False
        remaining = schedule.remaining_reschedule_tokens

        if reschedule_type == RescheduleType.FARMER_REQUEST:
            if remaining <= 0:
                return RescheduleResult(
                    subscription_id=schedule.subscription_id,
                    mission_id=mission_id,
                    old_date=old_date,
                    new_date=new_date,
                    reschedule_type=reschedule_type,
                    token_consumed=False,
                    remaining_tokens=remaining,
                    success=False,
                    reason="Yeniden planlama hakkı kalmadı.",
                )
            token_consumed = True
            remaining -= 1

        # Weather block token tüketmez (KR-015-5: force majeure)

        return RescheduleResult(
            subscription_id=schedule.subscription_id,
            mission_id=mission_id,
            old_date=old_date,
            new_date=new_date,
            reschedule_type=reschedule_type,
            token_consumed=token_consumed,
            remaining_tokens=remaining,
            success=True,
            reason="Yeniden planlama başarılı.",
        )

    def calculate_remaining_analyses(
        self,
        schedule: SubscriptionSchedule,
        as_of_date: date,
    ) -> int:
        """Belirli bir tarih itibarıyla kalan analiz sayısını hesaplar.

        Args:
            schedule: Abonelik takvimi.
            as_of_date: Referans tarih.

        Returns:
            Kalan analiz sayısı.
        """
        return sum(1 for a in schedule.analyses if a.scheduled_date >= as_of_date)

    def get_next_analysis(
        self,
        schedule: SubscriptionSchedule,
        as_of_date: date,
    ) -> ScheduledAnalysis | None:
        """Bir sonraki planlanmış analizi döner.

        Args:
            schedule: Abonelik takvimi.
            as_of_date: Referans tarih.

        Returns:
            Sonraki analiz veya None.
        """
        future = [a for a in schedule.analyses if a.scheduled_date >= as_of_date]
        if not future:
            return None
        return min(future, key=lambda a: a.scheduled_date)

    def _validate_config(self, config: SubscriptionConfig) -> None:
        """Abonelik yapılandırmasını doğrular."""
        if config.start_date > config.end_date:
            raise SubscriptionPlanningError("start_date, end_date'den sonra olamaz.")
        if config.interval_days <= 0:
            raise SubscriptionPlanningError("interval_days > 0 olmalıdır.")
        if config.total_analyses <= 0:
            raise SubscriptionPlanningError("total_analyses > 0 olmalıdır.")
        if config.reschedule_tokens < 0:
            raise SubscriptionPlanningError("reschedule_tokens negatif olamaz.")

        # Takvim uygunluk kontrolü: yeterli gün var mı?
        available_days = (config.end_date - config.start_date).days + 1
        required_days = (config.total_analyses - 1) * config.interval_days + 1
        if required_days > available_days:
            raise SubscriptionPlanningError(
                f"Yetersiz süre: {config.total_analyses} analiz için "
                f"{required_days} gün gerekli, {available_days} gün mevcut."
            )
