# PATH: src/core/domain/events/subscription_events.py
# DESC: Subscription domain event'leri (SubscriptionCreated, SubscriptionActivated, MissionScheduled, SubscriptionCompleted).

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from src.core.domain.events.base import DomainEvent


@dataclass(frozen=True)
class SubscriptionCreated(DomainEvent):
    """Sezonluk paket aboneliği oluşturuldu (KR-015-5).

    Fiyat snapshot alınır (KR-022).
    """

    subscription_id: uuid.UUID = field(default_factory=uuid.uuid4)
    field_id: uuid.UUID = field(default_factory=uuid.uuid4)
    crop_type: str = ""
    start_date: date | None = None
    end_date: date | None = None
    interval_days: int = 0
    total_analyses: int = 0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "subscription_id": str(self.subscription_id),
                "field_id": str(self.field_id),
                "crop_type": self.crop_type,
                "start_date": self.start_date.isoformat() if self.start_date else None,
                "end_date": self.end_date.isoformat() if self.end_date else None,
                "interval_days": self.interval_days,
                "total_analyses": self.total_analyses,
            }
        )
        return base


@dataclass(frozen=True)
class SubscriptionActivated(DomainEvent):
    """Abonelik aktifleştirildi (ödeme onaylandıktan sonra)."""

    subscription_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "subscription_id": str(self.subscription_id),
            }
        )
        return base


@dataclass(frozen=True)
class MissionScheduled(DomainEvent):
    """Abonelik kapsamında görev planlandı (KR-015-5).

    Takvim görünümü: computed schedule.
    """

    subscription_id: uuid.UUID = field(default_factory=uuid.uuid4)
    mission_id: uuid.UUID = field(default_factory=uuid.uuid4)
    scheduled_date: date | None = None

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "subscription_id": str(self.subscription_id),
                "mission_id": str(self.mission_id),
                "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            }
        )
        return base


@dataclass(frozen=True)
class SubscriptionCompleted(DomainEvent):
    """Abonelik tamamlandı (tüm analizler bitti)."""

    subscription_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "subscription_id": str(self.subscription_id),
            }
        )
        return base


@dataclass(frozen=True)
class SubscriptionRescheduled(DomainEvent):
    """Abonelik takvimi yeniden planlandı (KR-015-5).

    reschedule_type: farmer_request | system_reschedule (weather block).
    Weather block (force majeure) reschedule token tüketmez.
    """

    subscription_id: uuid.UUID = field(default_factory=uuid.uuid4)
    mission_id: uuid.UUID = field(default_factory=uuid.uuid4)
    old_date: date | None = None
    new_date: date | None = None
    reschedule_type: str = ""  # farmer_request | system_reschedule

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "subscription_id": str(self.subscription_id),
                "mission_id": str(self.mission_id),
                "old_date": self.old_date.isoformat() if self.old_date else None,
                "new_date": self.new_date.isoformat() if self.new_date else None,
                "reschedule_type": self.reschedule_type,
            }
        )
        return base
