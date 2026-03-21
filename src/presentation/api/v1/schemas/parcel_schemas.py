# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# PATH: src/presentation/api/v1/schemas/parcel_schemas.py
# DESC: Parcel lookup request/response schema.

from __future__ import annotations

from decimal import Decimal
from typing import Literal, Optional

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


class ParcelLookupRequest(SchemaBase):
    # KR-013: cadastral parcel lookup by province/district/village/ada/parsel.
    province: str = Field(min_length=2, max_length=64)
    district: str = Field(min_length=2, max_length=64)
    village: str = Field(min_length=2, max_length=64)
    ada: str = Field(min_length=1, max_length=32)
    parsel: str = Field(min_length=1, max_length=32)

    @field_validator("ada", "parsel", mode="before")
    @classmethod
    def normalize_numeric_ref(cls, value: str | int) -> str:
        return str(value).strip()


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ParcelResponse(SchemaBase):
    province: str
    district: str
    village: str
    ada: str
    parsel: str
    geometry: Optional[GeoJSONPolygon | GeoJSONMultiPolygon] = None
    area_m2: Optional[Decimal] = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    found: bool = True
    source: Optional[str] = Field(default=None, min_length=2, max_length=64)
    corr_id: Optional[str] = Field(default=None, min_length=8, max_length=128)
