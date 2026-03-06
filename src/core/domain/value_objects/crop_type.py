# PATH: src/core/domain/value_objects/crop_type.py
# DESC: CropType VO; bitki tipi enum + CropOpsProfile entegrasyonu.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar


class CropTypeError(Exception):
    """CropType domain invariant ihlali."""


@dataclass(frozen=True)
class CropType:
    """Bitki tipi değer nesnesi (KR-015, KR-081).

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    SSOT'a göre desteklenen bitki tipleri ve önerilen tarama aralıkları:
    - PAMUK (Cotton): 7-10 gün
    - ANTEP_FISTIGI (Pistachio): 10-15 gün
    - MISIR (Corn): 15-20 gün
    - BUGDAY (Wheat): 10-15 gün
    - AYCICEGI (Sunflower): 7-10 gün
    - UZUM (Grape): 7-10 gün
    - ZEYTIN (Olive): 15-20 gün
    - KIRMIZI_MERCIMEK (Red Lentil): 10-15 gün

    Invariants:
    - code, tanımlı geçerli bitki tiplerinden biri olmalıdır.
    """

    code: str

    # Sabit bitki tipi kodları
    PAMUK: ClassVar[str] = "PAMUK"
    ANTEP_FISTIGI: ClassVar[str] = "ANTEP_FISTIGI"
    MISIR: ClassVar[str] = "MISIR"
    BUGDAY: ClassVar[str] = "BUGDAY"
    AYCICEGI: ClassVar[str] = "AYCICEGI"
    UZUM: ClassVar[str] = "UZUM"
    ZEYTIN: ClassVar[str] = "ZEYTIN"
    KIRMIZI_MERCIMEK: ClassVar[str] = "KIRMIZI_MERCIMEK"

    _VALID_CODES: ClassVar[frozenset[str]] = frozenset(
        {
            "PAMUK",
            "ANTEP_FISTIGI",
            "MISIR",
            "BUGDAY",
            "AYCICEGI",
            "UZUM",
            "ZEYTIN",
            "KIRMIZI_MERCIMEK",
        }
    )

    # Bitki tipi -> Türkçe görünen ad eşlemesi
    _DISPLAY_NAMES: ClassVar[dict[str, str]] = {
        "PAMUK": "Pamuk",
        "ANTEP_FISTIGI": "Antep Fıstığı",
        "MISIR": "Mısır",
        "BUGDAY": "Buğday",
        "AYCICEGI": "Ayçiçeği",
        "UZUM": "Üzüm",
        "ZEYTIN": "Zeytin",
        "KIRMIZI_MERCIMEK": "Kırmızı Mercimek",
    }

    # Önerilen tarama aralıkları (gün): (min, max)
    _SCAN_INTERVALS: ClassVar[dict[str, tuple[int, int]]] = {
        "PAMUK": (7, 10),
        "ANTEP_FISTIGI": (10, 15),
        "MISIR": (15, 20),
        "BUGDAY": (10, 15),
        "AYCICEGI": (7, 10),
        "UZUM": (7, 10),
        "ZEYTIN": (15, 20),
        "KIRMIZI_MERCIMEK": (10, 15),
    }

    def __post_init__(self) -> None:
        if not isinstance(self.code, str):
            raise CropTypeError(f"code str olmalıdır, alınan tip: {type(self.code).__name__}")
        normalized = self.code.strip().upper()
        if normalized != self.code:
            object.__setattr__(self, "code", normalized)
        if self.code not in self._VALID_CODES:
            raise CropTypeError(f"Geçersiz bitki tipi: '{self.code}'. Geçerli değerler: {sorted(self._VALID_CODES)}")

    @property
    def display_name(self) -> str:
        """Türkçe görünen ad."""
        return self._DISPLAY_NAMES[self.code]

    @property
    def recommended_scan_interval(self) -> tuple[int, int]:
        """Önerilen tarama aralığı (min_gün, max_gün)."""
        return self._SCAN_INTERVALS[self.code]

    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return {
            "code": self.code,
            "display_name": self.display_name,
        }

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return f"CropType(code='{self.code}')"
