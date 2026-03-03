# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/entities/mission.py
# DESC: Mission; odeme dogrulama (KR-033), ucus, veri yukleme, analiz dispatch.
# SSOT: KR-028 (mission yasam dongusu), KR-033 (odeme hard gate)
"""
Mission domain entity.

Bir tarlanin belirli bir tarihte yapilacak tek analiz gorevi.
Tek seferlik talepten veya yillik abonelikten olusabilir (KR-028).
PAID olmadan Mission ASSIGNED olamaz (KR-033 Kural-1).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class MissionStatus(str, Enum):
    """KR-028 kanonik mission durumlari."""

    PLANNED = "PLANNED"
    ASSIGNED = "ASSIGNED"
    ACKED = "ACKED"
    FLOWN = "FLOWN"
    UPLOADED = "UPLOADED"
    ANALYZING = "ANALYZING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AssignmentSource(str, Enum):
    """KR-015-2: Mission atama kaynagi (sistem tohumlamasi vs. cekme kotasi)."""

    SYSTEM_SEED = "SYSTEM_SEED"
    PULL = "PULL"


class AssignmentReason(str, Enum):
    """KR-015-3/KR-015-4: Mission atama nedeni (otomatik sevk, admin override, yeniden atama)."""

    AUTO_DISPATCH = "AUTO_DISPATCH"
    ADMIN_OVERRIDE = "ADMIN_OVERRIDE"
    REASSIGNMENT = "REASSIGNMENT"


# KR-028: Gecerli durum gecisleri
_VALID_TRANSITIONS: dict[MissionStatus, set[MissionStatus]] = {
    MissionStatus.PLANNED: {MissionStatus.ASSIGNED, MissionStatus.FAILED, MissionStatus.CANCELLED},
    MissionStatus.ASSIGNED: {MissionStatus.ACKED, MissionStatus.FAILED, MissionStatus.CANCELLED},
    MissionStatus.ACKED: {MissionStatus.FLOWN, MissionStatus.FAILED, MissionStatus.CANCELLED},
    MissionStatus.FLOWN: {MissionStatus.UPLOADED, MissionStatus.FAILED, MissionStatus.CANCELLED},
    MissionStatus.UPLOADED: {MissionStatus.ANALYZING, MissionStatus.FAILED, MissionStatus.CANCELLED},
    MissionStatus.ANALYZING: {MissionStatus.DONE, MissionStatus.FAILED, MissionStatus.CANCELLED},
    MissionStatus.DONE: set(),
    MissionStatus.FAILED: set(),
    MissionStatus.CANCELLED: set(),
}


@dataclass
class Mission:
    """Analiz gorevi domain entity'si.

    * KR-028 -- Mission yasam dongusu ve SLA alanlari.
    * KR-033 -- Odeme dogrulama hard gate (PAID olmadan ASSIGNED olamaz).
    """

    mission_id: uuid.UUID
    field_id: uuid.UUID
    requested_by_user_id: uuid.UUID
    crop_type: str
    analysis_type: str
    status: MissionStatus
    price_snapshot_id: uuid.UUID
    created_at: datetime
    subscription_id: Optional[uuid.UUID] = None
    payment_intent_id: Optional[uuid.UUID] = None
    pilot_id: Optional[uuid.UUID] = None
    planned_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    flown_at: Optional[datetime] = None
    uploaded_at: Optional[datetime] = None
    analyzed_at: Optional[datetime] = None
    # KR-015: Sezonluk zamanlama penceresi ve atama meta verisi
    schedule_window_start: Optional[datetime] = None
    schedule_window_end: Optional[datetime] = None
    assignment_source: Optional[AssignmentSource] = None
    assignment_reason: Optional[AssignmentReason] = None

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if not self.crop_type:
            raise ValueError("crop_type is required")
        if not self.analysis_type:
            raise ValueError("analysis_type is required")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _transition_status(self, new_status: MissionStatus) -> None:
        """Validate and apply a status transition (KR-028)."""
        allowed = _VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid status transition: {self.status.value} -> {new_status.value}. "
                f"Allowed: {sorted(s.value for s in allowed)}"
            )
        self.status = new_status

    # ------------------------------------------------------------------
    # Domain methods
    # ------------------------------------------------------------------
    def assign_pilot(self, pilot_id: uuid.UUID) -> None:
        """Goreve pilot ata (KR-028, KR-033).

        KR-033 hard gate: PAID olmadan ASSIGNED olamaz.
        Odeme dogrulamasi caller (application service) sorumlulugundadir;
        entity yalnizca durum gecis kuralini uygular.
        """
        self._transition_status(MissionStatus.ASSIGNED)
        self.pilot_id = pilot_id

    def acknowledge(self) -> None:
        """Pilot gorevi onaylar (ASSIGNED -> ACKED)."""
        self._transition_status(MissionStatus.ACKED)

    def mark_flown(self, flown_at: Optional[datetime] = None) -> None:
        """Ucus tamamlandi (ACKED -> FLOWN)."""
        self._transition_status(MissionStatus.FLOWN)
        self.flown_at = flown_at or datetime.now(timezone.utc)

    def mark_uploaded(self, uploaded_at: Optional[datetime] = None) -> None:
        """Veri yuklendi (FLOWN -> UPLOADED)."""
        self._transition_status(MissionStatus.UPLOADED)
        self.uploaded_at = uploaded_at or datetime.now(timezone.utc)

    def start_analysis(self) -> None:
        """Analiz basladi (UPLOADED -> ANALYZING)."""
        self._transition_status(MissionStatus.ANALYZING)

    def complete(self, analyzed_at: Optional[datetime] = None) -> None:
        """Analiz tamamlandi (ANALYZING -> DONE)."""
        self._transition_status(MissionStatus.DONE)
        self.analyzed_at = analyzed_at or datetime.now(timezone.utc)

    def fail(self) -> None:
        """Gorev basarisiz oldu (herhangi bir aktif durum -> FAILED)."""
        self._transition_status(MissionStatus.FAILED)

    def cancel(self) -> None:
        """Gorev iptal edildi (herhangi bir aktif durum -> CANCELLED)."""
        self._transition_status(MissionStatus.CANCELLED)
