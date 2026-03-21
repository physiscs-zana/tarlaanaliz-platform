# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# PATH: src/presentation/api/v1/schemas/field_schemas.py
# DESC: Field request/response schema (KR-013).

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class GeoJSONPolygon(SchemaBase):
    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[list[float]]] = Field(min_length=1)


class GeoJSONMultiPolygon(SchemaBase):
    type: Literal["MultiPolygon"] = "MultiPolygon"
    coordinates: list[list[list[list[float]]]] = Field(min_length=1)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CreateFieldRequest(SchemaBase):
    # KR-013: field registration with cadastral parcel reference.
    province: str = Field(min_length=2, max_length=64)
    district: str = Field(min_length=2, max_length=64)
    village: str = Field(min_length=2, max_length=64)
    block_no: str = Field(min_length=1, max_length=32, description="Ada numarasi")
    parcel_no: str = Field(min_length=1, max_length=32, description="Parsel numarasi")
    area_m2: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    crop_type: Optional[str] = Field(default=None, min_length=2, max_length=64)
    geometry: Optional[GeoJSONPolygon | GeoJSONMultiPolygon] = None

    @field_validator("block_no", "parcel_no", mode="before")
    @classmethod
    def normalize_numeric_ref(cls, value: str | int) -> str:
        return str(value).strip()


class UpdateFieldRequest(SchemaBase):
    crop_type: Optional[str] = Field(default=None, min_length=2, max_length=64)
    area_m2: Optional[Decimal] = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    geometry: Optional[GeoJSONPolygon | GeoJSONMultiPolygon] = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class FieldResponse(SchemaBase):
    field_id: UUID
    user_id: UUID
    province: str
    district: str
    village: str
    block_no: str
    parcel_no: str
    area_m2: Decimal
    crop_type: Optional[str] = None
    field_code: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)


class PaginationMeta(SchemaBase):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class FieldListResponse(SchemaBase):
    items: list[FieldResponse] = Field(default_factory=list)
    pagination: PaginationMeta
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)


class FieldListFilter(SchemaBase):
    user_id: Optional[UUID] = None
    crop_type: Optional[str] = None
    province: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)

    @field_validator("page_size")
    @classmethod
    def normalize_page_size(cls, value: int) -> int:
        return min(value, 200)
