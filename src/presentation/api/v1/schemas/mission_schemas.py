# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# PATH: src/presentation/api/v1/schemas/mission_schemas.py
# DESC: Mission request/response schema (KR-028).

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class MissionStatus(str, Enum):
    PLANNED = "PLANNED"
    ASSIGNED = "ASSIGNED"
    ACKED = "ACKED"
    FLOWN = "FLOWN"
    UPLOADED = "UPLOADED"
    ANALYZING = "ANALYZING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class CropType(str, Enum):
    PAMUK = "PAMUK"
    ANTEP_FISTIGI = "ANTEP_FISTIGI"
    MISIR = "MISIR"
    BUGDAY = "BUGDAY"
    AYCICEGI = "AYCICEGI"
    UZUM = "UZUM"
    ZEYTIN = "ZEYTIN"
    KIRMIZI_MERCIMEK = "KIRMIZI_MERCIMEK"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CreateMissionRequest(SchemaBase):
    # KR-028: single analysis task for a field.
    field_id: UUID
    crop_type: CropType
    analysis_type: str = Field(default="MULTISPECTRAL", min_length=2, max_length=50)
    planned_at: Optional[datetime] = None
    subscription_id: Optional[UUID] = None


class UpdateMissionRequest(SchemaBase):
    status: Optional[MissionStatus] = None
    pilot_id: Optional[UUID] = None
    planned_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class MissionResponse(SchemaBase):
    mission_id: UUID
    field_id: UUID
    requested_by_user_id: UUID
    crop_type: str
    analysis_type: str
    status: MissionStatus
    subscription_id: Optional[UUID] = None
    payment_intent_id: Optional[UUID] = None
    pilot_id: Optional[UUID] = None
    price_snapshot_id: Optional[UUID] = None
    planned_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    flown_at: Optional[datetime] = None
    uploaded_at: Optional[datetime] = None
    analyzed_at: Optional[datetime] = None
    created_at: datetime
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)


class PaginationMeta(SchemaBase):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class MissionListFilter(SchemaBase):
    field_id: Optional[UUID] = None
    pilot_id: Optional[UUID] = None
    status: Optional[MissionStatus] = None
    crop_type: Optional[CropType] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)


class MissionListResponse(SchemaBase):
    items: list[MissionResponse] = Field(default_factory=list)
    pagination: PaginationMeta
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)
