# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# PATH: src/presentation/api/v1/schemas/expert_review_schemas.py
# DESC: Expert review request/response schema (KR-019, KR-029).

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ExpertReviewStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


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
# Request schemas
# ---------------------------------------------------------------------------

class SubmitVerdictRequest(SchemaBase):
    # KR-019: expert submits verdict and optional training grade for KR-029 feedback loop.
    verdict: Verdict
    training_grade: Optional[TrainingGrade] = None
    grade_reason: Optional[str] = Field(default=None, max_length=200)


class CreateExpertReviewRequest(SchemaBase):
    # KR-019: admin/system assigns a review to an expert for a mission analysis result.
    mission_id: UUID
    expert_id: UUID
    analysis_result_id: UUID


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ExpertReviewResponse(SchemaBase):
    review_id: UUID
    mission_id: UUID
    expert_id: UUID
    analysis_result_id: UUID
    status: ExpertReviewStatus
    assigned_at: datetime
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verdict: Optional[str] = None
    training_grade: Optional[str] = None
    grade_reason: Optional[str] = None
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)


class PaginationMeta(SchemaBase):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class ExpertReviewListResponse(SchemaBase):
    items: list[ExpertReviewResponse] = Field(default_factory=list)
    pagination: PaginationMeta
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)
