# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""KR-015 — RescheduleService.

Amaç: Sezonluk abonelikte sınırlı gün değiştirme (reschedule token) akışını yönetmek.
"""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass
class RescheduleResult:
    ok: bool
    reason: str
    new_date: Optional[str] = None
    token_remaining: Optional[int] = None


class RescheduleService:
    def __init__(self, pilot_availability: PilotAvailability):
        self.pilot_availability = pilot_availability

    def reschedule(self, subscription: SubscriptionLike, mission: MissionLike, new_date_iso: str) -> RescheduleResult:
        if subscription.reschedule_tokens_remaining <= 0:
            return RescheduleResult(ok=False, reason="NO_TOKENS")

        # TODO: compare new_date_iso inside window (start/end); parse dates as needed
        # Here we keep it string-based scaffold.
        if new_date_iso < mission.schedule_window_start or new_date_iso > mission.schedule_window_end:
            return RescheduleResult(ok=False, reason="OUT_OF_WINDOW")

        if mission.assigned_pilot_id:
            if not self.pilot_availability.is_available(mission.assigned_pilot_id, new_date_iso):
                return RescheduleResult(ok=False, reason="PILOT_NOT_AVAILABLE")

        # TODO: persist changes + decrement token + add audit + notify
        return RescheduleResult(
            ok=True,
            reason="OK",
            new_date=new_date_iso,
            token_remaining=subscription.reschedule_tokens_remaining - 1,
        )
