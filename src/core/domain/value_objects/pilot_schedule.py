"""KR-015 — PilotSchedule value object.

Amaç: Pilot çalışma günleri + kapasite doğrulamasının TEK noktası.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class PilotSchedule:
    work_days: FrozenSet[int]  # 0=Mon ... 6=Sun (örnek; projede netleştir)
    daily_capacity_donum: int  # 2500–3000
    system_seed_quota_donum: int = 1500  # seed kota, kalan pull

    effective_from: str = ""  # ISO8601 date-time or date (opsiyonel)

    def validate(self) -> None:
        if len(self.work_days) == 0:
            raise ValueError("work_days cannot be empty")
        if len(self.work_days) > 6:
            raise ValueError("work_days cannot exceed 6 days per week")
        if not (2500 <= self.daily_capacity_donum <= 3000):
            raise ValueError("daily_capacity_donum must be between 2500 and 3000")
        if not (0 < self.system_seed_quota_donum <= self.daily_capacity_donum):
            raise ValueError("system_seed_quota_donum must be <= daily_capacity_donum and > 0")

    def pull_quota_donum(self) -> int:
        # remaining quota for farmer-pull assignments
        return max(0, self.daily_capacity_donum - self.system_seed_quota_donum)
