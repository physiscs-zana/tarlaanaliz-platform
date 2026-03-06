# PATH: src/core/domain/events/training_feedback_events.py
# DESC: Training feedback domain event'leri; feedback loop (KR-019).

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from src.core.domain.events.base import DomainEvent


@dataclass(frozen=True)
class TrainingFeedbackSubmitted(DomainEvent):
    """Uzman eğitim geri bildirimi gönderildi (KR-019).

    training_grade: A|B|C|D|REJECT
    grade_reason: max 200 karakter.
    PII içermez.
    """

    feedback_id: uuid.UUID = field(default_factory=uuid.uuid4)
    expert_id: uuid.UUID = field(default_factory=uuid.uuid4)
    analysis_job_id: uuid.UUID = field(default_factory=uuid.uuid4)
    training_grade: str = ""  # A | B | C | D | REJECT
    grade_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "feedback_id": str(self.feedback_id),
                "expert_id": str(self.expert_id),
                "analysis_job_id": str(self.analysis_job_id),
                "training_grade": self.training_grade,
                "grade_reason": self.grade_reason,
            }
        )
        return base


@dataclass(frozen=True)
class TrainingFeedbackAccepted(DomainEvent):
    """Eğitim geri bildirimi kabul edildi ve model pipeline'a aktarılmaya hazır."""

    feedback_id: uuid.UUID = field(default_factory=uuid.uuid4)
    analysis_job_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "feedback_id": str(self.feedback_id),
                "analysis_job_id": str(self.analysis_job_id),
            }
        )
        return base


@dataclass(frozen=True)
class TrainingFeedbackRejected(DomainEvent):
    """Eğitim geri bildirimi reddedildi (kalite kontrolden geçemedi)."""

    feedback_id: uuid.UUID = field(default_factory=uuid.uuid4)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "feedback_id": str(self.feedback_id),
                "reason": self.reason,
            }
        )
        return base


@dataclass(frozen=True)
class TrainingDataExported(DomainEvent):
    """Eğitim verisi export edildi (admin only, PII yok, KR-019)."""

    export_id: uuid.UUID = field(default_factory=uuid.uuid4)
    record_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "export_id": str(self.export_id),
                "record_count": self.record_count,
            }
        )
        return base
