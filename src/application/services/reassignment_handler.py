"""KR-015 — Reassignment handler (mission -> REASSIGN_QUEUE + auto_dispatch).

Bu dosya dokümanda "YENİ veya GÜNCELLEME" olarak geçiyor.
Burada scaffold olarak veriyorum; var olan bir dosyan varsa merge et.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from ...core.domain.services.auto_dispatcher import AutoDispatcher, DispatchDecision


class MissionLike(Protocol):
    id: str
    territory_id: str
    scheduled_date: str
    area_donum: int


class PilotLike(Protocol):
    id: str
    territory_id: str
    reliability_score: float
    work_days: list[int]
    daily_capacity_donum: int


class MissionRepo(Protocol):
    def list_reassign_queue(self) -> Sequence[MissionLike]: ...
    def list_available_pilots(self) -> Sequence[PilotLike]: ...
    def mark_reassigned(self, mission_id: str, pilot_id: str) -> None: ...


@dataclass
class ReassignmentHandler:
    mission_repo: MissionRepo
    auto_dispatcher: AutoDispatcher

    def run_once(self) -> Sequence[DispatchDecision]:
        missions = self.mission_repo.list_reassign_queue()
        pilots = self.mission_repo.list_available_pilots()
        decisions = self.auto_dispatcher.dispatch(missions, pilots)
        for d in decisions:
            self.mission_repo.mark_reassigned(d.mission_id, d.pilot_id)
        return decisions
