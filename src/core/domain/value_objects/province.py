# PATH: src/core/domain/value_objects/province.py
# DESC: Province VO; Turkiye il listesi (81 il) ve KR-083 bolge yetkisi.
# SSOT: KR-083 (bolge bazli yetkilendirme)
"""
Province value object.

Turkiye'nin 81 ilini temsil eden immutable VO.
KR-083 bolge yetkisi kontrollerinde kullanilir;
il kodu (plaka) ve il adi eslemesi icerir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Turkiye 81 il: plaka kodu -> il adi
_PROVINCES: dict[int, str] = {
    1: "ADANA",
    2: "ADIYAMAN",
    3: "AFYONKARAHISAR",
    4: "AGRI",
    5: "AMASYA",
    6: "ANKARA",
    7: "ANTALYA",
    8: "ARTVIN",
    9: "AYDIN",
    10: "BALIKESIR",
    11: "BILECIK",
    12: "BINGOL",
    13: "BITLIS",
    14: "BOLU",
    15: "BURDUR",
    16: "BURSA",
    17: "CANAKKALE",
    18: "CANKIRI",
    19: "CORUM",
    20: "DENIZLI",
    21: "DIYARBAKIR",
    22: "EDIRNE",
    23: "ELAZIG",
    24: "ERZINCAN",
    25: "ERZURUM",
    26: "ESKISEHIR",
    27: "GAZIANTEP",
    28: "GIRESUN",
    29: "GUMUSHANE",
    30: "HAKKARI",
    31: "HATAY",
    32: "ISPARTA",
    33: "MERSIN",
    34: "ISTANBUL",
    35: "IZMIR",
    36: "KARS",
    37: "KASTAMONU",
    38: "KAYSERI",
    39: "KIRKLARELI",
    40: "KIRSEHIR",
    41: "KOCAELI",
    42: "KONYA",
    43: "KUTAHYA",
    44: "MALATYA",
    45: "MANISA",
    46: "KAHRAMANMARAS",
    47: "MARDIN",
    48: "MUGLA",
    49: "MUS",
    50: "NEVSEHIR",
    51: "NIGDE",
    52: "ORDU",
    53: "RIZE",
    54: "SAKARYA",
    55: "SAMSUN",
    56: "SIIRT",
    57: "SINOP",
    58: "SIVAS",
    59: "TEKIRDAG",
    60: "TOKAT",
    61: "TRABZON",
    62: "TUNCELI",
    63: "SANLIURFA",
    64: "USAK",
    65: "VAN",
    66: "YOZGAT",
    67: "ZONGULDAK",
    68: "AKSARAY",
    69: "BAYBURT",
    70: "KARAMAN",
    71: "KIRIKKALE",
    72: "BATMAN",
    73: "SIRNAK",
    74: "BARTIN",
    75: "ARDAHAN",
    76: "IGDIR",
    77: "YALOVA",
    78: "KARABUK",
    79: "KILIS",
    80: "OSMANIYE",
    81: "DUZCE",
}

# Ters esleme: il adi -> plaka kodu
_NAME_TO_CODE: dict[str, int] = {name: code for code, name in _PROVINCES.items()}

# Gecerli plaka kodlari seti
VALID_PROVINCE_CODES: frozenset[int] = frozenset(_PROVINCES.keys())


@dataclass(frozen=True)
class Province:
    """Immutable il degeri.

    * KR-083 -- Bolge bazli yetkilendirme; il kodu ile kontrol.

    frozen=True: olusturulduktan sonra alanlari degistirilemez.
    """

    code: int  # Plaka kodu (1-81)
    name: str  # Il adi (buyuk harf, ASCII)

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if self.code not in _PROVINCES:
            raise ValueError(f"Invalid province code: {self.code}. Must be 1-81.")
        expected_name = _PROVINCES[self.code]
        if self.name.upper() != expected_name:
            raise ValueError(f"Province name mismatch: code {self.code} expects '{expected_name}', got '{self.name}'")
        # Normalize name to uppercase
        object.__setattr__(self, "name", self.name.upper())

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------
    @classmethod
    def from_code(cls, code: int) -> Province:
        """Plaka kodundan Province olustur."""
        if code not in _PROVINCES:
            raise ValueError(f"Invalid province code: {code}. Must be 1-81.")
        return cls(code=code, name=_PROVINCES[code])

    @classmethod
    def from_name(cls, name: str) -> Province:
        """Il adindan Province olustur (case-insensitive)."""
        upper_name = name.strip().upper()
        code = _NAME_TO_CODE.get(upper_name)
        if code is None:
            raise ValueError(f"Unknown province name: '{name}'")
        return cls(code=code, name=upper_name)

    @classmethod
    def find_by_name(cls, name: str) -> Optional[Province]:
        """Il adi ile arama (bulunamazsa None doner)."""
        upper_name = name.strip().upper()
        code = _NAME_TO_CODE.get(upper_name)
        if code is None:
            return None
        return cls(code=code, name=upper_name)

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------
    @staticmethod
    def all_codes() -> frozenset[int]:
        """Tum gecerli plaka kodlari."""
        return VALID_PROVINCE_CODES

    @staticmethod
    def all_provinces() -> list[Province]:
        """81 ilin tamamini doner (plaka koduna gore sirali)."""
        return [Province(code=code, name=name) for code, name in sorted(_PROVINCES.items())]

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "name": self.name,
        }
