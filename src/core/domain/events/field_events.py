# PATH: src/core/domain/events/field_events.py
# DESC: Field domain event'leri (FieldCreated, FieldUpdated, FieldCropUpdated, FieldDeleted).

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from src.core.domain.events.base import DomainEvent


@dataclass(frozen=True)
class FieldCreated(DomainEvent):
    """Yeni tarla kaydedildi.

    Tekil kayıt kuralı: aynı il+ilçe+mahalle/köy+ada+parsel ikinci kez kaydedilemez.
    """

    field_id: uuid.UUID = field(default_factory=uuid.uuid4)
    owner_id: uuid.UUID = field(default_factory=uuid.uuid4)
    province_code: str = ""
    district: str = ""
    area_m2: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "field_id": str(self.field_id),
                "owner_id": str(self.owner_id),
                "province_code": self.province_code,
                "district": self.district,
                "area_m2": self.area_m2,
            }
        )
        return base


@dataclass(frozen=True)
class FieldUpdated(DomainEvent):
    """Tarla bilgileri güncellendi."""

    field_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "field_id": str(self.field_id),
            }
        )
        return base


@dataclass(frozen=True)
class FieldCropUpdated(DomainEvent):
    """Tarla bitki türü güncellendi.

    Yılda 1 defa, sadece 1 Ekim - 31 Aralık aralığında değiştirilebilir.
    """

    field_id: uuid.UUID = field(default_factory=uuid.uuid4)
    old_crop_type: str = ""
    new_crop_type: str = ""
    season_year: int = 0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "field_id": str(self.field_id),
                "old_crop_type": self.old_crop_type,
                "new_crop_type": self.new_crop_type,
                "season_year": self.season_year,
            }
        )
        return base


@dataclass(frozen=True)
class FieldDeleted(DomainEvent):
    """Tarla silindi (soft-delete)."""

    field_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "field_id": str(self.field_id),
            }
        )
        return base
