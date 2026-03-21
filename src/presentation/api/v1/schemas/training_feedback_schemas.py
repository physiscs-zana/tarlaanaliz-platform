# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# PATH: src/presentation/api/v1/schemas/training_feedback_schemas.py
# DESC: Training feedback export schema (KR-029).

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class Verdict(str, Enum):
    confirmed = "confirmed"
    corrected = "corrected"
    rejected = "rejected"
    needs_more_expert = "needs_more_expert"


class TrainingGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    REJECT = "REJECT"


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class TrainingFeedbackResponse(SchemaBase):
    # KR-029: training feedback export — review data + verdict + grade for ML pipeline.
    feedback_id: UUID
    review_id: UUID
    mission_id: UUID
    model_id: str
    verdict: Verdict
    training_grade: TrainingGrade
    corrected_class: Optional[str] = None
    notes: Optional[str] = None
    time_spent_seconds: Optional[int] = Field(default=None, ge=0)
    grade_reason: Optional[str] = Field(default=None, max_length=200)
    expert_confidence: Optional[Decimal] = Field(default=None, ge=0, le=1, max_digits=4, decimal_places=3)
    image_quality: Optional[Decimal] = Field(default=None, ge=0, le=1, max_digits=4, decimal_places=3)
    no_conflict: Optional[bool] = None
    created_at: datetime
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)


class PaginationMeta(SchemaBase):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class TrainingFeedbackListResponse(SchemaBase):
    items: list[TrainingFeedbackResponse] = Field(default_factory=list)
    pagination: PaginationMeta
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)
