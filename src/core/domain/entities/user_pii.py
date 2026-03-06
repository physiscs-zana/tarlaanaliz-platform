# PATH: src/core/domain/entities/user_pii.py
# DESC: UserPII; KVKK uyumlu hassas veri (PII) izolasyonu.
# SSOT: KR-066 (guvenlik ve KVKK), KR-063 (RBAC)
"""
UserPII domain entity.

KVKK uyumu geregi PII alanlari operasyonel veriden ayri tutulur (KR-066).
Il operatoru ve saha rolleri bu entity'ye ERISMEZ.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class UserPII:
    """Kullaniciya ait hassas kisisel veriler (PII).

    * KR-066 -- PII ayri veri alaninda tutulur; raporlama katmani pseudonymous.
    * KR-063 -- Yalnizca CENTRAL_ADMIN erisebilir.
    """

    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    full_name: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    iban_encrypted: Optional[str] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _touch(self) -> None:
        """Stamp updated_at to current UTC time."""
        self.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Domain methods
    # ------------------------------------------------------------------
    def update_name(self, full_name: str) -> None:
        """Kullanici ad-soyad guncelleme."""
        if not full_name or not full_name.strip():
            raise ValueError("full_name cannot be empty")
        self.full_name = full_name.strip()
        self._touch()

    def update_iban(self, iban_encrypted: str) -> None:
        """Sifrelenmis IBAN guncelleme (KR-066: PII vault'ta tutulur)."""
        if not iban_encrypted or not iban_encrypted.strip():
            raise ValueError("iban_encrypted cannot be empty")
        self.iban_encrypted = iban_encrypted
        self._touch()
