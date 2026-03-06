# PATH: src/core/domain/entities/price_snapshot.py
# DESC: PriceSnapshot (immutable); odeme/abonelik tutarlarinin degismemesi garantisi.
# SSOT: KR-022 (fiyat yonetimi politikasi), KR-033 (odeme akisi)
"""
PriceSnapshot domain entity (immutable / frozen).

Fiyatlar PriceBook'tan gelir; siparis/abonelik olusurken snapshot siparise yazilir.
Gecmis siparislerin fiyati sonradan DEGISMEZ (KR-022).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class PriceSnapshot:
    """Degismez fiyat snapshot'i.

    * KR-022 -- Versiyonlu + tarih aralikli fiyat yonetimi.
    * KR-033 -- Siparis/abonelik olusurken fiyat snapshot siparise yazilir.

    frozen=True: olusturulduktan sonra alanlari degistirilemez.
    """

    price_snapshot_id: uuid.UUID
    crop_type: str
    analysis_type: str  # "single" | "seasonal"
    amount_kurus: int
    currency: str  # "TRY"
    effective_date: date
    created_at: datetime
    promotional_discount_percent: Optional[Decimal] = None
    effective_until: Optional[date] = None
    created_by_admin_user_id: Optional[uuid.UUID] = None

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        # frozen=True prevents normal assignment; use object.__setattr__ for validation
        if not self.crop_type:
            raise ValueError("crop_type is required")
        if self.analysis_type not in ("single", "seasonal"):
            raise ValueError(f"analysis_type must be 'single' or 'seasonal', got '{self.analysis_type}'")
        if self.amount_kurus <= 0:
            raise ValueError("amount_kurus must be positive")
        if self.currency != "TRY":
            raise ValueError(f"currency must be 'TRY', got '{self.currency}'")
        if self.promotional_discount_percent is not None and not (
            Decimal("0") <= self.promotional_discount_percent <= Decimal("100")
        ):
            raise ValueError("promotional_discount_percent must be 0-100")

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------
    def is_active(self, as_of: date) -> bool:
        """Bu snapshot verilen tarihte gecerli mi?"""
        if as_of < self.effective_date:
            return False
        if self.effective_until is not None and as_of > self.effective_until:
            return False
        return True

    def discounted_amount_kurus(self) -> int:
        """Promosyon indirimi uygulanmis tutar (kurus)."""
        if self.promotional_discount_percent is None:
            return self.amount_kurus
        discount = self.amount_kurus * self.promotional_discount_percent / Decimal("100")
        return int(self.amount_kurus - discount)
