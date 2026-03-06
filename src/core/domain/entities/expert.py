# PATH: src/core/domain/entities/expert.py
# DESC: Expert; curated onboarding, specialization, kota, bolge yetkisi (KR-019).
# SSOT: KR-019 (expert portal / uzman inceleme)
"""
Expert domain entity.

Uzman hesabi self-signup DEGILDIR: ADMIN kontrollu acilir (curated onboarding).
Uzman yalnizca kendisine atanmis incelemeleri gorur (ownership check zorunlu).
PII GORUNMEZ (KR-019).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List


class ExpertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


@dataclass
class Expert:
    """Uzman domain entity'si.

    * KR-019 -- Expert Portal: curated onboarding, uzmanlik alanlari, kota.
    * KR-063 -- Rol kodu: EXPERT (yalnizca atanmis incelemeleri gorur).
    """

    expert_id: uuid.UUID
    user_id: uuid.UUID
    province: str
    max_daily_quota: int
    created_by_admin_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    specialization: List[str] = field(default_factory=list)
    status: ExpertStatus = ExpertStatus.ACTIVE

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if not self.province or not self.province.strip():
            raise ValueError("province is required")
        if self.max_daily_quota <= 0:
            raise ValueError("max_daily_quota must be positive")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Domain methods
    # ------------------------------------------------------------------
    def add_specialization(self, spec: str) -> None:
        """Uzmanlik alani ekle (ornegin 'cotton_disease', 'pest')."""
        if not spec or not spec.strip():
            raise ValueError("specialization cannot be empty")
        spec = spec.strip()
        if spec in self.specialization:
            raise ValueError(f"Specialization '{spec}' already exists")
        self.specialization.append(spec)
        self._touch()

    def remove_specialization(self, spec: str) -> None:
        """Uzmanlik alani kaldir."""
        if spec not in self.specialization:
            raise ValueError(f"Specialization '{spec}' not found")
        self.specialization.remove(spec)
        self._touch()

    def suspend(self) -> None:
        """Uzmani askiya al."""
        if self.status == ExpertStatus.SUSPENDED:
            raise ValueError("Expert is already suspended")
        self.status = ExpertStatus.SUSPENDED
        self._touch()

    def activate(self) -> None:
        """Uzmani aktif et."""
        if self.status == ExpertStatus.ACTIVE:
            raise ValueError("Expert is already active")
        self.status = ExpertStatus.ACTIVE
        self._touch()
