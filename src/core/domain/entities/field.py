# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/entities/field.py
# DESC: Field; geometri (polygon) + parsel referansi + sezon bitkisi.
# SSOT: KR-013 (ciftci uyeligi / tarla yonetimi), KR-016 (eslestirme), KR-080 (teknik kurallar)
"""
Field domain entity.

Her tarla icin il, ilce, mahalle/koy, ada, parsel ve alan (m2) tutulur.
Tekil kayit kurali: il+ilce+mahalle/koy+ada+parsel kombinasyonu tekrar edemez.
Bitki turu degisimi: yilda 1 defa, sadece 1 Ekim - 31 Aralik (KR-013).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional


class FieldStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass
class Field:
    """Tarla domain entity'si.

    * KR-013 -- Tarla kaydi ve bitki turu yonetimi.
    * KR-016 -- Drone-tarla-bitki eslestirme politikasi.
    * KR-080 -- Teknik kurallar (tekil kayit, bitki degisim penceresi).
    """

    field_id: uuid.UUID
    user_id: uuid.UUID
    province: str
    district: str
    village: str
    ada: str
    parsel: str
    area_m2: Decimal
    status: FieldStatus
    created_at: datetime
    updated_at: datetime
    crop_type: Optional[str] = None
    crop_type_updated_at: Optional[date] = None
    geometry: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------
    @property
    def parcel_ref(self) -> str:
        """Benzersiz parsel referansi (composite key). PII degildir."""
        return f"{self.province}/{self.district}/{self.village}/{self.ada}/{self.parsel}"

    @property
    def area_donum(self) -> Decimal:
        """Alan m2'den donume cevrilir (1 donum = 1000 m2). KR-021."""
        return self.area_m2 / Decimal("1000")

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if not self.province or not self.province.strip():
            raise ValueError("province is required")
        if not self.district or not self.district.strip():
            raise ValueError("district is required")
        if not self.village or not self.village.strip():
            raise ValueError("village is required")
        if not self.ada or not self.ada.strip():
            raise ValueError("ada is required")
        if not self.parsel or not self.parsel.strip():
            raise ValueError("parsel is required")
        if self.area_m2 is None or self.area_m2 <= 0:
            raise ValueError("area_m2 must be positive")
        # KR-013: GeoJSON geometry validation
        if self.geometry is not None:
            self._validate_geometry(self.geometry)

    @staticmethod
    def _validate_geometry(geo: Dict[str, Any]) -> None:
        """Validate GeoJSON structure for field boundary."""
        if not isinstance(geo, dict):
            raise ValueError("geometry must be a GeoJSON dict")
        geo_type = geo.get("type")
        if geo_type not in ("Polygon", "MultiPolygon"):
            raise ValueError(f"geometry.type must be Polygon or MultiPolygon, got: {geo_type}")
        coords = geo.get("coordinates")
        if not coords or not isinstance(coords, list):
            raise ValueError("geometry.coordinates is required and must be a list")
        if geo_type == "Polygon":
            if not coords or not isinstance(coords[0], list):
                raise ValueError("Polygon coordinates must be a list of rings")
            ring = coords[0]
            if len(ring) < 4:
                raise ValueError("Polygon ring must have at least 4 coordinate pairs")
            if ring[0] != ring[-1]:
                raise ValueError("Polygon ring must be closed (first == last coordinate)")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Domain methods
    # ------------------------------------------------------------------
    def change_crop_type(self, new_crop_type: str, as_of: date) -> None:
        """Bitki turu degistir (KR-013, KR-080).

        Kurallar:
        - Yalnizca 1 Ekim -- 31 Aralik arasinda.
        - Yilda yalnizca 1 defa.
        Backend tarih disinda degisikligi ENGELLER.
        """
        if not new_crop_type or not new_crop_type.strip():
            raise ValueError("new_crop_type cannot be empty")

        # KR-013: Sadece 1 Ekim - 31 Aralik
        if as_of.month < 10:
            raise ValueError(
                f"Bitki turu degisikligi yalnizca 1 Ekim - 31 Aralik arasinda "
                f"yapilabilir (KR-013). Guncel tarih: {as_of}"
            )

        # KR-013: Yilda yalnizca 1 defa
        if self.crop_type_updated_at is not None:
            if self.crop_type_updated_at.year == as_of.year:
                raise ValueError(
                    f"Bitki turu bu yil ({as_of.year}) icinde zaten degistirildi "
                    f"(son degisiklik: {self.crop_type_updated_at}). "
                    f"Yilda yalnizca 1 defa degistirilebilir (KR-013)."
                )

        self.crop_type = new_crop_type.strip()
        self.crop_type_updated_at = as_of
        self._touch()
