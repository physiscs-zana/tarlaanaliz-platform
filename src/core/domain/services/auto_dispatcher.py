# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
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


@dataclass
class DispatchDecision:
    mission_id: str
    pilot_id: str
    policy: AssignmentPolicy


class AutoDispatcher:
    def __init__(self, lookahead_days: int = 7):
        self.lookahead_days = lookahead_days

    def dispatch(self, missions: Sequence[MissionLike], pilots: Sequence[PilotLike]) -> List[DispatchDecision]:
        # TODO: Replace this naive heuristic with your real constraints:
        # - work_days
        # - daily_capacity
        # - SLA priority
        decisions: List[DispatchDecision] = []
        pilots_by_territory: dict[str, list[PilotLike]] = {}
        for p in pilots:
            pilots_by_territory.setdefault(p.territory_id, []).append(p)

        for m in missions:
            cand = pilots_by_territory.get(m.territory_id, [])
            if not cand:
                continue
            # pick best reliability
            cand_sorted = sorted(cand, key=lambda x: getattr(x, "reliability_score", 0.0), reverse=True)
            chosen = cand_sorted[0]
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
