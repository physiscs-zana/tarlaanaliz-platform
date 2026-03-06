# PATH: src/core/domain/value_objects/price_snapshot.py
# DESC: PriceSnapshot VO.
# SSOT: KR-022 (fiyat yonetimi), KR-033 (odeme akisi)
"""
PriceSnapshot value object.

Siparis/abonelik olusturken yazilan degismez fiyat bilgisi.
Entity katmanindaki PriceSnapshot entity'si tam kaydi temsil eder;
bu VO, domain genelinde fiyat referansi olarak tasinabilir
hafif (lightweight) bir degerdir (KR-022).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from src.core.domain.value_objects.money import CurrencyCode, Money


@dataclass(frozen=True)
class PriceSnapshotRef:
    """Immutable fiyat snapshot referansi.

    * KR-022 -- Versiyonlu fiyat yonetimi; gecmis fiyat degismez.
    * KR-033 -- Odeme akisinda snapshot siparise yazilir.

    frozen=True: olusturulduktan sonra alanlari degistirilemez.
    Entity'den farkli olarak yalnizca tasinabilir referans alanlari icerir.
    """

    price_snapshot_id: uuid.UUID
    crop_type: str
    analysis_type: str  # "single" | "seasonal"
    amount_kurus: int
    currency: CurrencyCode
    effective_date: date
    promotional_discount_percent: Optional[Decimal] = None

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if not self.crop_type:
            raise ValueError("crop_type is required")
        if self.analysis_type not in ("single", "seasonal"):
            raise ValueError(f"analysis_type must be 'single' or 'seasonal', got '{self.analysis_type}'")
        if self.amount_kurus <= 0:
            raise ValueError("amount_kurus must be positive")
        if self.promotional_discount_percent is not None and not (
            Decimal("0") <= self.promotional_discount_percent <= Decimal("100")
        ):
            raise ValueError("promotional_discount_percent must be 0-100")

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------
    def to_money(self) -> Money:
        """Money VO'ya donustur."""
        return Money(amount_kurus=self.amount_kurus, currency=self.currency)

    def discounted_amount_kurus(self) -> int:
        """Promosyon indirimi uygulanmis tutar (kurus)."""
        if self.promotional_discount_percent is None:
            return self.amount_kurus
        discount = self.amount_kurus * self.promotional_discount_percent / Decimal("100")
        return int(self.amount_kurus - discount)

    def discounted_money(self) -> Money:
        """Indirimli tutari Money VO olarak doner."""
        return Money(
            amount_kurus=self.discounted_amount_kurus(),
            currency=self.currency,
        )

    def is_active(self, as_of: date) -> bool:
        """Bu snapshot verilen tarihte gecerli mi?"""
        return as_of >= self.effective_date

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "price_snapshot_id": str(self.price_snapshot_id),
            "crop_type": self.crop_type,
            "analysis_type": self.analysis_type,
            "amount_kurus": self.amount_kurus,
            "currency": self.currency.value,
            "effective_date": self.effective_date.isoformat(),
        }
        if self.promotional_discount_percent is not None:
            result["promotional_discount_percent"] = str(self.promotional_discount_percent)
        return result
