# PATH: src/core/domain/entities/feedback_record.py
# DESC: FeedbackRecord; training feedback ve ground truth etiket kalitesi (KR-019).
# SSOT: KR-029 (YZ egitim geri bildirimi), KR-019 (expert portal)
"""
FeedbackRecord domain entity.

Uzman duzeltmelerini YZ modeline geri beslemek ve model iyilestirmesi yapmak (KR-029).
expert_reviews -> uzman portal UI icin; feedback_records -> YZ training pipeline icin.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


_VALID_VERDICTS = frozenset({"confirmed", "corrected", "rejected", "needs_more_expert"})
_VALID_TRAINING_GRADES = frozenset({"A", "B", "C", "D", "REJECT"})


@dataclass
class FeedbackRecord:
    """YZ egitim geri bildirim kaydi.

    * KR-029 -- Training Feedback Loop: uzman feedback'lerini standart formatta
      export ederek model egitim pipeline'ina aktarmak.
    * KR-019 -- Expert verdict + training_grade.

    Dogrulama kurallari (SSOT SQL):
    - verdict='corrected' ise corrected_class ZORUNLU.
    - verdict in ('corrected', 'rejected') ise notes ZORUNLU.
    - grade_reason max 200 karakter.
    """

    feedback_id: uuid.UUID
    review_id: uuid.UUID
    mission_id: uuid.UUID
    model_id: str
    verdict: str  # confirmed|corrected|rejected|needs_more_expert
    training_grade: str  # A|B|C|D|REJECT
    created_at: datetime
    corrected_class: Optional[str] = None
    notes: Optional[str] = None
    time_spent_seconds: Optional[int] = None
    grade_reason: Optional[str] = None
    expert_confidence: Optional[Decimal] = None  # numeric(4,3) -> 0-1
    image_quality: Optional[Decimal] = None  # numeric(4,3) -> 0-1
    no_conflict: Optional[bool] = None

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("model_id is required")

        # Verdict validation
        if self.verdict not in _VALID_VERDICTS:
            raise ValueError(f"Invalid verdict: '{self.verdict}'. Must be one of: {sorted(_VALID_VERDICTS)}")

        # Training grade validation
        if self.training_grade not in _VALID_TRAINING_GRADES:
            raise ValueError(
                f"Invalid training_grade: '{self.training_grade}'. Must be one of: {sorted(_VALID_TRAINING_GRADES)}"
            )

        # KR-029: verdict=corrected ise corrected_class ZORUNLU
        if self.verdict == "corrected":
            if not self.corrected_class or not self.corrected_class.strip():
                raise ValueError("corrected_class is required when verdict='corrected' (KR-029)")

        # KR-029: verdict in (corrected, rejected) ise notes ZORUNLU
        if self.verdict in ("corrected", "rejected"):
            if not self.notes or not self.notes.strip():
                raise ValueError(f"notes is required when verdict='{self.verdict}' (KR-029)")

        # grade_reason max 200 karakter
        if self.grade_reason and len(self.grade_reason) > 200:
            raise ValueError("grade_reason must be at most 200 characters")

        # Decimal range validations
        if self.expert_confidence is not None:
            if not (Decimal("0") <= self.expert_confidence <= Decimal("1")):
                raise ValueError("expert_confidence must be between 0 and 1")

        if self.image_quality is not None:
            if not (Decimal("0") <= self.image_quality <= Decimal("1")):
                raise ValueError("image_quality must be between 0 and 1")
