# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""KR-015 — AutoDispatcher (rule-based, no AI).

Amaç: Yaklaşan mission'ları pilotlara kural bazlı atamak.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol, Sequence

from ..value_objects.assignment_policy import AssignmentPolicy, AssignmentSource, AssignmentReason


class MissionLike(Protocol):
    id: str
    territory_id: str  # or region key
    scheduled_date: str
    area_donum: int


class PilotLike(Protocol):
    id: str
    territory_id: str
    reliability_score: float
    work_days: list[int]  # 0=Mon, 6=Sun
    daily_capacity_donum: int


@dataclass
class DispatchDecision:
    mission_id: str
    pilot_id: str
    policy: AssignmentPolicy


class AutoDispatcher:
    def __init__(self, lookahead_days: int = 7):
        self.lookahead_days = lookahead_days

    def dispatch(self, missions: Sequence[MissionLike], pilots: Sequence[PilotLike]) -> List[DispatchDecision]:
        """KR-015: Rule-based pilot dispatch with capacity and work_day enforcement."""
        decisions: List[DispatchDecision] = []
        pilots_by_territory: dict[str, list[PilotLike]] = {}
        for p in pilots:
            pilots_by_territory.setdefault(p.territory_id, []).append(p)

        # Track remaining daily capacity per pilot
        pilot_remaining: dict[str, int] = {p.id: getattr(p, "daily_capacity_donum", 100) for p in pilots}

        for m in missions:
            cand = pilots_by_territory.get(m.territory_id, [])
            if not cand:
                continue

            # Filter by work_days: only pilots who work on the mission's scheduled day
            scheduled_weekday = -1
            try:
                from datetime import date as _date

                d = _date.fromisoformat(m.scheduled_date)
                scheduled_weekday = d.weekday()
            except (ValueError, TypeError):
                pass

            eligible = []
            for p in cand:
                # KR-015: Check work_days
                work_days = getattr(p, "work_days", list(range(7)))
                if scheduled_weekday >= 0 and scheduled_weekday not in work_days:
                    continue
                # KR-015-1: Check remaining capacity
                remaining = pilot_remaining.get(p.id, 0)
                if remaining < m.area_donum:
                    continue
                eligible.append(p)

            if not eligible:
                continue

            # Pick best reliability among eligible
            eligible_sorted = sorted(eligible, key=lambda x: getattr(x, "reliability_score", 0.0), reverse=True)
            chosen = eligible_sorted[0]

            # Deduct capacity
            pilot_remaining[chosen.id] = pilot_remaining.get(chosen.id, 0) - m.area_donum

            decisions.append(
                DispatchDecision(
                    mission_id=m.id,
                    pilot_id=chosen.id,
                    policy=AssignmentPolicy(
                        source=AssignmentSource.SYSTEM_SEED,
                        reason=AssignmentReason.AUTO_DISPATCH,
                    ),
                )
            )
        return decisions
