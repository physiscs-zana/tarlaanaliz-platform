# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# PATH: src/presentation/api/v1/schemas/subscription_schemas.py
# DESC: Subscription request/response schema (KR-027).

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class SubscriptionStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class SubscriptionPlanType(str, Enum):
    SEASONAL = "SEASONAL"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CreateSubscriptionRequest(SchemaBase):
    # KR-027: seasonal subscription for periodic mission generation.
    field_id: UUID
    crop_type: str = Field(min_length=2, max_length=64)
    analysis_type: str = Field(default="MULTISPECTRAL", min_length=2, max_length=50)
    interval_days: int = Field(ge=1, le=365)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self) -> CreateSubscriptionRequest:
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class UpdateSubscriptionRequest(SchemaBase):
    status: Optional[SubscriptionStatus] = None
    interval_days: Optional[int] = Field(default=None, ge=1, le=365)
    end_date: Optional[date] = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class SubscriptionResponse(SchemaBase):
    subscription_id: UUID
    farmer_user_id: UUID
    field_id: UUID
    crop_type: str
    analysis_type: str
    interval_days: int
    start_date: date
    end_date: date
    next_due_at: Optional[datetime] = None
    status: SubscriptionStatus
    plan_type: SubscriptionPlanType = SubscriptionPlanType.SEASONAL
    price_snapshot_id: Optional[UUID] = None
    payment_intent_id: Optional[UUID] = None
    reschedule_tokens_per_season: int = 2
    reschedule_tokens_used: int = 0
    created_at: datetime
    updated_at: datetime
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)


class PaginationMeta(SchemaBase):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class SubscriptionListResponse(SchemaBase):
    items: list[SubscriptionResponse] = Field(default_factory=list)
    pagination: PaginationMeta
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)
