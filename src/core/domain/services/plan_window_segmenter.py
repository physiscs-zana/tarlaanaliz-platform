# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""KR-015 — PlanWindowSegmenter.

Amaç: Büyük alanlarda (örn. 10.000 dönüm) aynı pencere içinde çoklu pilotla yürütme için segmentleme.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class MissionSegment:
    segment_no: int
    area_donum: int
    assigned_pilot_id: str = ""  # optional at this stage


class PlanWindowSegmenter:
    def __init__(self, threshold_donum: int = 10000, segment_size_donum: int = 2500):
        self.threshold_donum = threshold_donum
        self.segment_size_donum = segment_size_donum

    def segment(self, total_area_donum: int) -> List[MissionSegment]:
        if total_area_donum <= self.threshold_donum:
            return [MissionSegment(segment_no=1, area_donum=total_area_donum)]

        segs: List[MissionSegment] = []
        remaining = total_area_donum
        no = 1
        while remaining > 0:
            chunk = min(self.segment_size_donum, remaining)
            segs.append(MissionSegment(segment_no=no, area_donum=chunk))
            remaining -= chunk
            no += 1
        return segs
