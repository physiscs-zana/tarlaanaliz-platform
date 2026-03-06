# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/entities/pilot.py
# DESC: Pilot; kapasite (work_days, daily_capacity), bolge atamasi, Drone.
# SSOT: TARLAANALIZ_SSOT_v1_2_0.txt — KR-015 (drone pilotlari), KR-015-1 (kapasite), KR-015-2 (seed/pull), KR-034 (drone bagimsizlik)
"""
Pilot domain entity.

v1.2.0 (KR-034): Pilot 5 onaylı modeli destekler:
  DJI_MAVIC_3M | DJI_M350_RTK_SENTERA_6X | WINGTRAONE_GEN2 | PARROT_SEQUOIA_PLUS | AGEAGLE_EBEE_X
Günlük kapasite 2500-3000 dönüm, varsayılan 2750 (KR-015-1).
SYSTEM_SEED_QUOTA varsayılan 1500, PULL_QUOTA = capacity - seed (KR-015-2).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import ClassVar, List, Optional


class PilotStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


# KR-015-1 sabitleri
_MIN_DAILY_CAPACITY_DONUM = 2500
_MAX_DAILY_CAPACITY_DONUM = 3000
_DEFAULT_DAILY_CAPACITY_DONUM = 2750
_DEFAULT_SYSTEM_SEED_QUOTA = 1500
_MAX_WORK_DAYS = 6
_EMERGENCY_OVERFLOW_RATIO = Decimal("1.10")


@dataclass
class Pilot:
    """Drone pilotu domain entity'si.

    * KR-015   -- Pilot kayit, drone modeli, seri no, veri teslimi.
    * KR-015-1 -- Calisma gunleri ve gunluk kapasite.
    * KR-015-2 -- Seed + Pull is dagitim politikasi.
    * KR-015-3 -- Iptal / yeniden atama.
    * KR-034   -- DJI bağımsızlık planı; 4 onaylı model desteklenir.
    """

    # KR-034: Onaylı drone model ID'leri (drone_model alanı bunlardan biri olmalı)
    _APPROVED_DRONE_MODELS: ClassVar[frozenset[str]] = frozenset({
        "DJI_MAVIC_3M",            # Phase 1, birincil
        "DJI_M350_RTK_SENTERA_6X", # Phase 1, KR-001 desteklenen model
        "WINGTRAONE_GEN2",          # Phase 2 Senaryo A/B
        "PARROT_SEQUOIA_PLUS",      # Phase 2 Senaryo A
        "AGEAGLE_EBEE_X",           # Phase 2 Senaryo B
    })

    pilot_id: uuid.UUID
    user_id: uuid.UUID
    province: str
    district: str
    full_name: str
    phone_number: str
    drone_model: str  # KR-034: DJI_MAVIC_3M | DJI_M350_RTK_SENTERA_6X | WINGTRAONE_GEN2 | PARROT_SEQUOIA_PLUS | AGEAGLE_EBEE_X
    drone_serial_number: str
    created_at: datetime
    updated_at: datetime
    work_days: List[int] = field(default_factory=list)  # 0=Mon .. 6=Sun
    daily_capacity_donum: int = _DEFAULT_DAILY_CAPACITY_DONUM
    system_seed_quota: int = _DEFAULT_SYSTEM_SEED_QUOTA
    province_list: List[str] = field(default_factory=list)
    status: PilotStatus = PilotStatus.ACTIVE
    reliability_score: Decimal = Decimal("1.0")

    # ------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------
    @property
    def pull_quota(self) -> int:
        """PULL_QUOTA = daily_capacity - seed (KR-015-2)."""
        return max(0, self.daily_capacity_donum - self.system_seed_quota)

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if not self.province or not self.province.strip():
            raise ValueError("province is required")
        if not self.full_name or not self.full_name.strip():
            raise ValueError("full_name is required")
        if not self.phone_number or not self.phone_number.strip():
            raise ValueError("phone_number is required")
        if not self.drone_serial_number or not self.drone_serial_number.strip():
            raise ValueError("drone_serial_number is required (KR-015)")
        if self.drone_model not in self._APPROVED_DRONE_MODELS:
            raise ValueError(
                f"drone_model '{self.drone_model}' onaylı listede yok (KR-034). "
                f"Geçerliler: {sorted(self._APPROVED_DRONE_MODELS)}"
            )
        if len(self.work_days) > _MAX_WORK_DAYS:
            raise ValueError(
                f"work_days cannot exceed {_MAX_WORK_DAYS} days (KR-015-1)"
            )
        if not (
            _MIN_DAILY_CAPACITY_DONUM
            <= self.daily_capacity_donum
            <= _MAX_DAILY_CAPACITY_DONUM
        ):
            raise ValueError(
                f"daily_capacity_donum must be {_MIN_DAILY_CAPACITY_DONUM}-"
                f"{_MAX_DAILY_CAPACITY_DONUM} (KR-015-1), got {self.daily_capacity_donum}"
            )
        if not (Decimal("0") <= self.reliability_score <= Decimal("1")):
            raise ValueError("reliability_score must be between 0 and 1")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Domain methods
    # ------------------------------------------------------------------
    def update_capacity(self, new_capacity: int) -> None:
        """Gunluk kapasiteyi guncelle (KR-015-1).

        Degisiklik 'gelecek hafta gecerli olacak sekilde' uygulanir;
        bu zamanlama kontrolu caller/scheduler sorumlulugundadir.
        """
        if not (_MIN_DAILY_CAPACITY_DONUM <= new_capacity <= _MAX_DAILY_CAPACITY_DONUM):
            raise ValueError(
                f"daily_capacity_donum must be {_MIN_DAILY_CAPACITY_DONUM}-"
                f"{_MAX_DAILY_CAPACITY_DONUM} (KR-015-1), got {new_capacity}"
            )
        self.daily_capacity_donum = new_capacity
        self._touch()

    def update_work_days(self, days: List[int]) -> None:
        """Haftalik calisma gunlerini guncelle (KR-015-1)."""
        if len(days) > _MAX_WORK_DAYS:
            raise ValueError(
                f"work_days cannot exceed {_MAX_WORK_DAYS} days (KR-015-1)"
            )
        for d in days:
            if d < 0 or d > 6:
                raise ValueError(f"Invalid day: {d}. Must be 0 (Mon) to 6 (Sun)")
        self.work_days = sorted(set(days))
        self._touch()

    def max_capacity_with_emergency(self) -> int:
        """Acil durum icin %10 tolerans (KR-015-1)."""
        return int(self.daily_capacity_donum * _EMERGENCY_OVERFLOW_RATIO)

    def degrade_reliability(self, penalty: Decimal) -> None:
        """Guvenilirlik skorunu dusur (KR-015-3: bildirimsiz no-show)."""
        if penalty < Decimal("0"):
            raise ValueError("penalty must be non-negative")
        new_score = max(Decimal("0"), self.reliability_score - penalty)
        self.reliability_score = new_score
        self._touch()

    def suspend(self) -> None:
        """Pilotu askiya al (KR-015-3: admin inceleme)."""
        if self.status == PilotStatus.SUSPENDED:
            raise ValueError("Pilot is already suspended")
        self.status = PilotStatus.SUSPENDED
        self._touch()

    def activate(self) -> None:
        """Pilotu aktif et."""
        if self.status == PilotStatus.ACTIVE:
            raise ValueError("Pilot is already active")
        self.status = PilotStatus.ACTIVE
        self._touch()

    def deactivate(self) -> None:
        """Pilotu pasif et."""
        if self.status == PilotStatus.INACTIVE:
            raise ValueError("Pilot is already inactive")
        self.status = PilotStatus.INACTIVE
        self._touch()
