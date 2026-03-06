# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/entities/user.py
# DESC: User; telefon + PIN kimlik dogrulama (email/TCKN/OTP yok).
# SSOT: TARLAANALIZ_SSOT_v1_2_0.txt — KR-050 (kimlik), KR-063 (13 rol, v1.2.0)
"""
User domain entity.

Kimlik modeli: telefon numarasi + 6 haneli PIN (KR-050).
Roller: KR-063 kanonik RBAC matrisi (v1.2.0: 13 rol).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    """KR-063 kanonik rol kodlari (v1.2.0 — 13 rol)."""

    FARMER_SINGLE = "FARMER_SINGLE"
    FARMER_MEMBER = "FARMER_MEMBER"
    COOP_OWNER = "COOP_OWNER"
    COOP_ADMIN = "COOP_ADMIN"
    COOP_AGRONOMIST = "COOP_AGRONOMIST"
    COOP_VIEWER = "COOP_VIEWER"
    PILOT = "PILOT"
    STATION_OPERATOR = "STATION_OPERATOR"
    IL_OPERATOR = "IL_OPERATOR"
    BILLING_ADMIN = "BILLING_ADMIN"
    CENTRAL_ADMIN = "CENTRAL_ADMIN"
    AI_SERVICE = "AI_SERVICE"
    EXPERT = "EXPERT"


@dataclass
class User:
    """Kullanici domain entity'si.

    * KR-050 -- Telefon + 6 haneli PIN kimlik dogrulama.
    * KR-063 -- RBAC roller.
    * KR-066 -- PII ayri tutulur; bu entity yalnizca operasyonel alanlari icerir.
    """

    user_id: uuid.UUID
    phone_number: str
    pin_hash: str
    role: UserRole
    province: str
    created_at: datetime
    updated_at: datetime
    must_reset_pin: bool = False
    coop_id: Optional[uuid.UUID] = None

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if not self.phone_number or not self.phone_number.strip():
            raise ValueError("phone_number is required (KR-050)")
        if not self.pin_hash or not self.pin_hash.strip():
            raise ValueError("pin_hash is required (KR-050)")
        if not self.province or not self.province.strip():
            raise ValueError("province is required")
        if not isinstance(self.role, UserRole):
            raise ValueError(f"role must be a UserRole enum, got {type(self.role)}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _touch(self) -> None:
        """Stamp updated_at to current UTC time."""
        self.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Domain methods
    # ------------------------------------------------------------------
    def reset_pin(self, new_pin_hash: str) -> None:
        """Admin/operator tarafindan PIN sifirlama (KR-050).

        Kullanici bir sonraki giriste yeni PIN belirler.
        """
        if not new_pin_hash or not new_pin_hash.strip():
            raise ValueError("new_pin_hash cannot be empty")
        self.pin_hash = new_pin_hash
        self.must_reset_pin = True
        self._touch()

    def change_pin(self, new_pin_hash: str) -> None:
        """Kullanicinin kendi PIN'ini degistirmesi (KR-050)."""
        if not new_pin_hash or not new_pin_hash.strip():
            raise ValueError("new_pin_hash cannot be empty")
        self.pin_hash = new_pin_hash
        self.must_reset_pin = False
        self._touch()

    def assign_role(self, new_role: UserRole) -> None:
        """Rol atama (KR-063). Audit log uretimi caller sorumlulugundadir."""
        if not isinstance(new_role, UserRole):
            raise ValueError(f"new_role must be UserRole, got {type(new_role)}")
        self.role = new_role
        self._touch()

    def link_to_coop(self, coop_id: uuid.UUID) -> None:
        """Kullaniciyi bir kooperatife bagla (KR-014)."""
        if self.coop_id is not None:
            raise ValueError(f"User {self.user_id} is already linked to coop {self.coop_id}. Unlink first.")
        self.coop_id = coop_id
        self._touch()

    def unlink_from_coop(self) -> None:
        """Kooperatif baglantisini kaldir."""
        if self.coop_id is None:
            raise ValueError(f"User {self.user_id} is not linked to any coop")
        self.coop_id = None
        self._touch()
