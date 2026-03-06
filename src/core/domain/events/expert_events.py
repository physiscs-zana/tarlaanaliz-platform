# PATH: src/core/domain/events/expert_events.py
# DESC: Expert domain event'leri (ExpertRegistered, ExpertActivated, FeedbackProvided).

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from src.core.domain.events.base import DomainEvent


@dataclass(frozen=True)
class ExpertRegistered(DomainEvent):
    """Uzman kaydı tamamlandı (KR-019).

    Admin kontrollü curated onboarding ile açılır.
    PII domain event'e taşınmaz.
    """

    expert_id: uuid.UUID = field(default_factory=uuid.uuid4)
    specializations: list[str] = field(default_factory=list)
    province_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "expert_id": str(self.expert_id),
                "specializations": self.specializations,
                "province_code": self.province_code,
            }
        )
        return base


@dataclass(frozen=True)
class ExpertActivated(DomainEvent):
    """Uzman hesabı aktifleştirildi (admin onayı sonrası)."""

    expert_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "expert_id": str(self.expert_id),
            }
        )
        return base


@dataclass(frozen=True)
class ExpertDeactivated(DomainEvent):
    """Uzman hesabı devre dışı bırakıldı."""

    expert_id: uuid.UUID = field(default_factory=uuid.uuid4)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "expert_id": str(self.expert_id),
                "reason": self.reason,
            }
        )
        return base


@dataclass(frozen=True)
class FeedbackProvided(DomainEvent):
    """Uzman geri bildirim verdi (KR-019).

    training_grade: A|B|C|D|REJECT
    grade_reason: max 200 karakter.
    """

    expert_id: uuid.UUID = field(default_factory=uuid.uuid4)
    review_id: uuid.UUID = field(default_factory=uuid.uuid4)
    training_grade: str = ""  # A | B | C | D | REJECT
    grade_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "expert_id": str(self.expert_id),
                "review_id": str(self.review_id),
                "training_grade": self.training_grade,
                "grade_reason": self.grade_reason,
            }
        )
        return base
