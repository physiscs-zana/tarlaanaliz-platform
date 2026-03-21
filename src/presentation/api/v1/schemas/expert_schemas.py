# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# PATH: src/presentation/api/v1/schemas/expert_schemas.py
# DESC: Expert request/response schema (KR-019).

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ExpertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CreateExpertRequest(SchemaBase):
    # KR-019: curated onboarding — admin creates expert with province and quota.
    user_id: UUID
    province: str = Field(min_length=2, max_length=64)
    max_daily_quota: int = Field(ge=1, le=100)
    specialization: list[str] = Field(default_factory=list, max_length=30)


class UpdateExpertRequest(SchemaBase):
    province: Optional[str] = Field(default=None, min_length=2, max_length=64)
    max_daily_quota: Optional[int] = Field(default=None, ge=1, le=100)
    specialization: Optional[list[str]] = Field(default=None, max_length=30)
    status: Optional[ExpertStatus] = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ExpertResponse(SchemaBase):
    expert_id: UUID
    user_id: UUID
    province: str
    max_daily_quota: int
    specialization: list[str] = Field(default_factory=list)
    status: ExpertStatus
    created_at: datetime
    updated_at: datetime
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)


class PaginationMeta(SchemaBase):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class ExpertListResponse(SchemaBase):
    items: list[ExpertResponse] = Field(default_factory=list)
    pagination: PaginationMeta
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)
