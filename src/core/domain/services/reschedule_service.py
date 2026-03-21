# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""KR-015 — RescheduleService.

Amaç: Sezonluk abonelikte sınırlı gün değiştirme (reschedule token) akışını yönetmek.
KR-015-5: Reschedule token kontrolu, tarih penceresi dogrulamasi, pilot musaitlik kontrolu.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol, Optional


class SubscriptionLike(Protocol):
    id: str
    reschedule_tokens_remaining: int


class MissionLike(Protocol):
    id: str
    scheduled_date: str
    schedule_window_start: str
    schedule_window_end: str
    assigned_pilot_id: Optional[str]


class PilotAvailability(Protocol):
    def is_available(self, pilot_id: str, date_iso: str) -> bool: ...


class RescheduleCallback(Protocol):
    """Reschedule isleminin kaliciligini saglayan callback protokolu.

    Domain service state persist etmez — caller (application service)
    bu callback uzerinden DB guncelleme, audit log ve bildirim yapar.
    """

    def apply_reschedule(
        self,
        subscription_id: str,
        mission_id: str,
        old_date: str,
        new_date: str,
        tokens_remaining: int,
    ) -> None: ...


@dataclass
class RescheduleResult:
    ok: bool
    reason: str
    new_date: Optional[str] = None
    token_remaining: Optional[int] = None


def _parse_date(date_str: str) -> date:
    """ISO tarih string'ini date objesine cevirir."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


class RescheduleService:
    """Sezonluk abonelik yeniden planlama servisi (KR-015-5).

    Sorumluluklar:
    - Token yeterliligi kontrolu
    - Yeni tarihin planlama penceresi icinde olup olmadigini dogrulama
    - Pilot musaitlik kontrolu (atanmis pilot varsa)
    - Persist islemini callback uzerinden tetikleme (domain service DB'ye dokunmaz)
    """

    def __init__(
        self,
        pilot_availability: PilotAvailability,
        callback: Optional[RescheduleCallback] = None,
    ):
        self.pilot_availability = pilot_availability
        self._callback = callback

    def reschedule(
        self,
        subscription: SubscriptionLike,
        mission: MissionLike,
        new_date_iso: str,
    ) -> RescheduleResult:
        """Gorevi yeni tarihe tasi.

        Adimlar:
        1. Token kontrolu (KR-015-5: sezon basi 2 token)
        2. Tarih penceresi dogrulamasi (window_start <= new_date <= window_end)
        3. Pilot musaitlik kontrolu (atanmis pilot varsa)
        4. Basarili ise callback ile persist et
        """
        # 1. Token kontrolu
        if subscription.reschedule_tokens_remaining <= 0:
            return RescheduleResult(ok=False, reason="NO_TOKENS")

        # 2. Tarih penceresi dogrulamasi — ISO string karsilastirmasi
        try:
            new_dt = _parse_date(new_date_iso)
            window_start = _parse_date(mission.schedule_window_start)
            window_end = _parse_date(mission.schedule_window_end)
        except (ValueError, TypeError):
            return RescheduleResult(ok=False, reason="INVALID_DATE_FORMAT")

        if new_dt < window_start or new_dt > window_end:
            return RescheduleResult(ok=False, reason="OUT_OF_WINDOW")

        # Mevcut tarihle ayni gun kontrolu
        if new_date_iso == mission.scheduled_date:
            return RescheduleResult(ok=False, reason="SAME_DATE")

        # 3. Pilot musaitlik kontrolu
        if mission.assigned_pilot_id:
            if not self.pilot_availability.is_available(mission.assigned_pilot_id, new_date_iso):
                return RescheduleResult(ok=False, reason="PILOT_NOT_AVAILABLE")

        tokens_remaining = subscription.reschedule_tokens_remaining - 1

        # 4. Persist — callback uzerinden DB guncelleme + audit log + bildirim
        if self._callback is not None:
            self._callback.apply_reschedule(
                subscription_id=subscription.id,
                mission_id=mission.id,
                old_date=mission.scheduled_date,
                new_date=new_date_iso,
                tokens_remaining=tokens_remaining,
            )

        return RescheduleResult(
            ok=True,
            reason="OK",
            new_date=new_date_iso,
            token_remaining=tokens_remaining,
        )
