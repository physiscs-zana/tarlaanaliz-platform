# PATH: src/core/domain/events/mission_events.py
# DESC: Mission domain event'leri (MissionAssigned, MissionStarted, DataUploaded, AnalysisRequested, MissionCompleted, MissionCancelled).

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from src.core.domain.events.base import DomainEvent


@dataclass(frozen=True)
class MissionAssigned(DomainEvent):
    """Görev pilota atandı (KR-015-2).

    assignment_source: SYSTEM_SEED | PULL
    PII içermez; MissionID + Field/ParcelRef + konum düzeyinde sunulur.
    """

    mission_id: uuid.UUID = field(default_factory=uuid.uuid4)
    pilot_id: uuid.UUID = field(default_factory=uuid.uuid4)
    field_id: uuid.UUID = field(default_factory=uuid.uuid4)
    assignment_source: str = ""  # SYSTEM_SEED | PULL

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "mission_id": str(self.mission_id),
                "pilot_id": str(self.pilot_id),
                "field_id": str(self.field_id),
                "assignment_source": self.assignment_source,
            }
        )
        return base


@dataclass(frozen=True)
class MissionStarted(DomainEvent):
    """Pilot görevi başlattı (uçuş başladı)."""

    mission_id: uuid.UUID = field(default_factory=uuid.uuid4)
    pilot_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "mission_id": str(self.mission_id),
                "pilot_id": str(self.pilot_id),
            }
        )
        return base


@dataclass(frozen=True)
class DataUploaded(DomainEvent):
    """Uçuş verileri yüklendi (istasyondan).

    Eşleştirme zorunlu: MissionID varsa öncelik, yoksa coğrafi kesişim.
    """

    mission_id: uuid.UUID = field(default_factory=uuid.uuid4)
    batch_id: uuid.UUID = field(default_factory=uuid.uuid4)
    pilot_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "mission_id": str(self.mission_id),
                "batch_id": str(self.batch_id),
                "pilot_id": str(self.pilot_id),
            }
        )
        return base


@dataclass(frozen=True)
class MissionAnalysisRequested(DomainEvent):
    """Görev için analiz talep edildi (KR-017)."""

    mission_id: uuid.UUID = field(default_factory=uuid.uuid4)
    field_id: uuid.UUID = field(default_factory=uuid.uuid4)
    crop_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "mission_id": str(self.mission_id),
                "field_id": str(self.field_id),
                "crop_type": self.crop_type,
            }
        )
        return base


@dataclass(frozen=True)
class MissionCompleted(DomainEvent):
    """Görev tamamlandı (uçuş + veri yükleme + analiz)."""

    mission_id: uuid.UUID = field(default_factory=uuid.uuid4)
    pilot_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "mission_id": str(self.mission_id),
                "pilot_id": str(self.pilot_id),
            }
        )
        return base


@dataclass(frozen=True)
class MissionCancelled(DomainEvent):
    """Görev iptal edildi (KR-015-3).

    cancel_reason: pilot_notice | admin_override | weather_block | no_show
    """

    mission_id: uuid.UUID = field(default_factory=uuid.uuid4)
    cancel_reason: str = ""
    cancelled_by: uuid.UUID | None = None

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "mission_id": str(self.mission_id),
                "cancel_reason": self.cancel_reason,
                "cancelled_by": str(self.cancelled_by) if self.cancelled_by else None,
            }
        )
        return base


@dataclass(frozen=True)
class MissionReplanQueued(DomainEvent):
    """Görev yeniden planlama kuyruğuna alındı (KR-015-3, KR-015-5).

    replan_reason: WEATHER_BLOCK | PILOT_CANCEL | ADMIN_OVERRIDE
    """

    mission_id: uuid.UUID = field(default_factory=uuid.uuid4)
    replan_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "mission_id": str(self.mission_id),
                "replan_reason": self.replan_reason,
            }
        )
        return base
