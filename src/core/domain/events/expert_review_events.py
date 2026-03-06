# PATH: src/core/domain/events/expert_review_events.py
# DESC: Expert review domain event'leri (KR-019).

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from src.core.domain.events.base import DomainEvent


@dataclass(frozen=True)
class ExpertReviewRequested(DomainEvent):
    """Düşük güven skoru nedeniyle uzman incelemesi talep edildi (KR-019).

    PII içermez; sadece analiz ve alan referansları.
    """

    review_id: uuid.UUID = field(default_factory=uuid.uuid4)
    analysis_job_id: uuid.UUID = field(default_factory=uuid.uuid4)
    field_id: uuid.UUID = field(default_factory=uuid.uuid4)
    assigned_expert_id: uuid.UUID | None = None
    confidence_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "review_id": str(self.review_id),
                "analysis_job_id": str(self.analysis_job_id),
                "field_id": str(self.field_id),
                "assigned_expert_id": str(self.assigned_expert_id) if self.assigned_expert_id else None,
                "confidence_score": self.confidence_score,
            }
        )
        return base


@dataclass(frozen=True)
class ExpertReviewAssigned(DomainEvent):
    """Uzman inceleme görevi atandı."""

    review_id: uuid.UUID = field(default_factory=uuid.uuid4)
    expert_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "review_id": str(self.review_id),
                "expert_id": str(self.expert_id),
            }
        )
        return base


@dataclass(frozen=True)
class ExpertReviewCompleted(DomainEvent):
    """Uzman inceleme tamamlandı (KR-019).

    decision: confirmed | corrected | rejected | needs_more_expert
    """

    review_id: uuid.UUID = field(default_factory=uuid.uuid4)
    expert_id: uuid.UUID = field(default_factory=uuid.uuid4)
    decision: str = ""  # confirmed | corrected | rejected | needs_more_expert

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "review_id": str(self.review_id),
                "expert_id": str(self.expert_id),
                "decision": self.decision,
            }
        )
        return base


@dataclass(frozen=True)
class ExpertReviewEscalated(DomainEvent):
    """Uzman inceleme yükseltildi (needs_more_expert)."""

    review_id: uuid.UUID = field(default_factory=uuid.uuid4)
    original_expert_id: uuid.UUID = field(default_factory=uuid.uuid4)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "review_id": str(self.review_id),
                "original_expert_id": str(self.original_expert_id),
                "reason": self.reason,
            }
        )
        return base
