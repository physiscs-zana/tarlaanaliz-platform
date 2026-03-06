# PATH: src/core/domain/value_objects/money.py
# DESC: Money VO; para birimi + miktar; fiyat snapshot immutability (KR-022).
# SSOT: KR-022 (fiyat yonetimi), KR-033 (odeme akisi)
"""
Money value object.

Para birimi ve miktari temsil eder; immutable (frozen=True).
Kurus cinsinden (int) tutar + para birimi kodu.
Negatif tutar kabul edilmez; karsilastirma ve aritmetik islemler
para birimi eslesmesi zorunluluguna tabidir (KR-022).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CurrencyCode(str, Enum):
    """Desteklenen para birimleri. Simdilik yalnizca TRY."""

    TRY = "TRY"


@dataclass(frozen=True)
class Money:
    """Immutable para degeri.

    * KR-022 -- Versiyonlu fiyat yonetimi; fiyat snapshot'larinda kullanilir.
    * KR-033 -- Odeme tutarlarinda kullanilir.

    frozen=True: olusturulduktan sonra alanlari degistirilemez.
    Tutar kurus cinsindendir (1 TL = 100 kurus). int kullanilarak
    floating-point yuvarlama hatalari onlenir.
    """

    amount_kurus: int
    currency: CurrencyCode

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if not isinstance(self.amount_kurus, int):
            raise TypeError(f"amount_kurus must be int, got {type(self.amount_kurus).__name__}")
        if self.amount_kurus < 0:
            raise ValueError("amount_kurus cannot be negative")
        if not isinstance(self.currency, CurrencyCode):
            raise TypeError(f"currency must be CurrencyCode, got {type(self.currency).__name__}")

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------
    @property
    def amount_lira(self) -> float:
        """Kurus -> lira donusumu (goruntuleme icin)."""
        return self.amount_kurus / 100

    @property
    def is_zero(self) -> bool:
        return self.amount_kurus == 0

    # ------------------------------------------------------------------
    # Aritmetik islemler
    # ------------------------------------------------------------------
    def add(self, other: Money) -> Money:
        """Iki Money toplama. Para birimi eslesmesi zorunludur."""
        self._assert_same_currency(other)
        return Money(
            amount_kurus=self.amount_kurus + other.amount_kurus,
            currency=self.currency,
        )

    def subtract(self, other: Money) -> Money:
        """Cikarma. Sonuc negatif olamaz."""
        self._assert_same_currency(other)
        result = self.amount_kurus - other.amount_kurus
        if result < 0:
            raise ValueError(
                f"Subtraction would result in negative amount: {self.amount_kurus} - {other.amount_kurus} = {result}"
            )
        return Money(amount_kurus=result, currency=self.currency)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(f"Currency mismatch: {self.currency.value} vs {other.currency.value}")

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, object]:
        return {
            "amount_kurus": self.amount_kurus,
            "currency": self.currency.value,
        }

    @classmethod
    def try_kurus(cls, amount_kurus: int) -> Money:
        """Fabrika: TRY cinsinden Money olustur."""
        return cls(amount_kurus=amount_kurus, currency=CurrencyCode.TRY)
