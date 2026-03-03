# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/value_objects/crop_scan_interval.py
# DESC: CropScanInterval VO; mahsul-özgü drone tarama aralıkları (KR-024).
"""
KR-024: Her mahsul tipi için min/max tarama aralığı (gün).
Abonelik planlama servisi bu değerleri kullanarak next_due_at hesaplar.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


class CropScanIntervalError(Exception):
    """CropScanInterval domain invariant ihlali."""


@dataclass(frozen=True)
class CropScanInterval:
    """Mahsul-özgü tarama aralığı (KR-024).

    Immutable; IO yok.

    KR-024 kanonik aralıklar (gün):
      PAMUK 7-10, MISIR 15-20, BUGDAY/AYCICEGI/KIRMIZI_MERCIMEK 10-14,
      UZUM 7-14, ZEYTIN/ANTEP_FISTIGI 14-21.
    """

    min_days: int
    max_days: int

    # KR-024 sabit aralıklar
    PAMUK: ClassVar[tuple[int, int]] = (7, 10)
    MISIR: ClassVar[tuple[int, int]] = (15, 20)
    BUGDAY: ClassVar[tuple[int, int]] = (10, 14)
    AYCICEGI: ClassVar[tuple[int, int]] = (10, 14)
    ZEYTIN: ClassVar[tuple[int, int]] = (14, 21)
    UZUM: ClassVar[tuple[int, int]] = (7, 14)
    ANTEP_FISTIGI: ClassVar[tuple[int, int]] = (14, 21)
    KIRMIZI_MERCIMEK: ClassVar[tuple[int, int]] = (10, 14)

    _CROP_INTERVALS: ClassVar[dict[str, tuple[int, int]]] = {
        "PAMUK": (7, 10),
        "MISIR": (15, 20),
        "BUGDAY": (10, 14),
        "AYCICEGI": (10, 14),
        "ZEYTIN": (14, 21),
        "UZUM": (7, 14),
        "ANTEP_FISTIGI": (14, 21),
        "KIRMIZI_MERCIMEK": (10, 14),
    }

    def __post_init__(self) -> None:
        if self.min_days <= 0:
            raise CropScanIntervalError(f"min_days pozitif olmalı: {self.min_days}")
        if self.max_days < self.min_days:
            raise CropScanIntervalError(
                f"max_days >= min_days olmalı: {self.max_days} < {self.min_days}"
            )

    @classmethod
    def for_crop(cls, crop_type: str) -> "CropScanInterval":
        """CropType string'inden interval oluştur (KR-024)."""
        key = crop_type.strip().upper()
        if key not in cls._CROP_INTERVALS:
            raise CropScanIntervalError(
                f"Geçersiz mahsul: '{crop_type}'. "
                f"Geçerliler: {sorted(cls._CROP_INTERVALS)}"
            )
        min_d, max_d = cls._CROP_INTERVALS[key]
        return cls(min_days=min_d, max_days=max_d)

    @property
    def default_days(self) -> int:
        """Varsayılan aralık (min+max ortalaması)."""
        return (self.min_days + self.max_days) // 2

    def is_within_interval(self, days_since_last: int) -> bool:
        return self.min_days <= days_since_last <= self.max_days

    def to_dict(self) -> dict[str, int]:
        return {"min_days": self.min_days, "max_days": self.max_days, "default_days": self.default_days}

    def __str__(self) -> str:
        return f"CropScanInterval({self.min_days}-{self.max_days} gün)"
