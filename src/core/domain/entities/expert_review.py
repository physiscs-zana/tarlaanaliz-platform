# PATH: src/core/domain/entities/expert_review.py
# DESC: ExpertReview; confidence esigi asilan analizlerin manuel incelemesi (KR-019).
# SSOT: KR-019 (expert portal / uzman inceleme), KR-029 (training feedback)
"""
ExpertReview domain entity.

Modelin dusuk guven verdigi veya celiskili durumlarda manuel inceleme (KR-019).
Uzman karar formati: confirmed | corrected | rejected | needs_more_expert.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ExpertReviewStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


_VALID_VERDICTS = frozenset({"confirmed", "corrected", "rejected", "needs_more_expert"})
_VALID_TRAINING_GRADES = frozenset({"A", "B", "C", "D", "REJECT"})


@dataclass
class ExpertReview:
    """Uzman incelemesi domain entity'si.

    * KR-019 -- Expert Portal: inceleme atama, durum takibi, verdict.
    * KR-029 -- Verdict, FeedbackRecord uzerinden YZ egitim pipeline'ina aktarilir.
    """

    review_id: uuid.UUID
    mission_id: uuid.UUID
    expert_id: uuid.UUID
    analysis_result_id: uuid.UUID
    status: ExpertReviewStatus
    assigned_at: datetime
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verdict: Optional[str] = None  # confirmed|corrected|rejected|needs_more_expert
    # KR-019: training_grade (A|B|C|D|REJECT) ve grade_reason (max 200 karakter)
    training_grade: Optional[str] = None
    grade_reason: Optional[str] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _touch(self) -> None:
        """No updated_at on this entity; use status timestamps instead."""
        pass

    # ------------------------------------------------------------------
    # Domain methods
    # ------------------------------------------------------------------
    def start_review(self) -> None:
        """Uzman incelemeye baslar (PENDING -> IN_PROGRESS)."""
        if self.status != ExpertReviewStatus.PENDING:
            raise ValueError(f"Can only start_review from PENDING, current: {self.status.value}")
        self.status = ExpertReviewStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)

    def submit_verdict(
        self,
        verdict: str,
        training_grade: Optional[str] = None,
        grade_reason: Optional[str] = None,
    ) -> None:
        """Uzman karari gonder (IN_PROGRESS -> COMPLETED|REJECTED).

        Gecerli verdict degerleri: confirmed, corrected, rejected, needs_more_expert.
        KR-019: training_grade (A|B|C|D|REJECT) ve grade_reason (max 200 karakter).
        """
        if self.status != ExpertReviewStatus.IN_PROGRESS:
            raise ValueError(f"Can only submit_verdict from IN_PROGRESS, current: {self.status.value}")
        if verdict not in _VALID_VERDICTS:
            raise ValueError(f"Invalid verdict: '{verdict}'. Must be one of: {sorted(_VALID_VERDICTS)}")
        if training_grade is not None and training_grade not in _VALID_TRAINING_GRADES:
            raise ValueError(
                f"Invalid training_grade: '{training_grade}'. Must be one of: {sorted(_VALID_TRAINING_GRADES)}"
            )
        if grade_reason is not None and len(grade_reason) > 200:
            raise ValueError("grade_reason must be at most 200 characters")
        self.verdict = verdict
        self.training_grade = training_grade
        self.grade_reason = grade_reason
        self.completed_at = datetime.now(timezone.utc)
        if verdict == "rejected":
            self.status = ExpertReviewStatus.REJECTED
        else:
            self.status = ExpertReviewStatus.COMPLETED
