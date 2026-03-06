# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Application DTOs for contract-first payload mapping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ExpertDashboardStatsDTO:
    pending_reviews: int
    completed_reviews: int
    avg_turnaround_minutes: float | None
    daily_review_limit: int | None

    def __post_init__(self) -> None:
        if self.pending_reviews < 0:
            raise ValueError("pending_reviews must be >= 0")
        if self.completed_reviews < 0:
            raise ValueError("completed_reviews must be >= 0")
        if self.daily_review_limit is not None and self.daily_review_limit < 0:
            raise ValueError("daily_review_limit must be >= 0")

    # TODO: decide if daily_review_limit should be per territory or global.


@dataclass(frozen=True, slots=True)
class ExpertDashboardDTO:
    expert_id: str
    stats: ExpertDashboardStatsDTO
    queue_items: tuple[str, ...]
    priority_mission_ids: tuple[str, ...]
    correlation_id: str | None

    # KR-081: stable read-model payload for dashboard mapping.
    def to_dict(self) -> dict[str, Any]:
        return {
            "expert_id": self.expert_id,
            "stats": {
                "pending_reviews": self.stats.pending_reviews,
                "completed_reviews": self.stats.completed_reviews,
                "avg_turnaround_minutes": self.stats.avg_turnaround_minutes,
                "daily_review_limit": self.stats.daily_review_limit,
            },
            "queue_items": list(self.queue_items),
            "priority_mission_ids": list(self.priority_mission_ids),
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ExpertDashboardDTO:
        raw_stats = payload["stats"]
        return cls(
            expert_id=str(payload["expert_id"]),
            stats=ExpertDashboardStatsDTO(
                pending_reviews=int(raw_stats["pending_reviews"]),
                completed_reviews=int(raw_stats["completed_reviews"]),
                avg_turnaround_minutes=(
                    None
                    if raw_stats.get("avg_turnaround_minutes") is None
                    else float(raw_stats["avg_turnaround_minutes"])
                ),
                daily_review_limit=(
                    None if raw_stats.get("daily_review_limit") is None else int(raw_stats["daily_review_limit"])
                ),
            ),
            queue_items=tuple(str(item) for item in payload.get("queue_items", [])),
            priority_mission_ids=tuple(str(item) for item in payload.get("priority_mission_ids", [])),
            correlation_id=None if payload.get("correlation_id") is None else str(payload["correlation_id"]),
        )
