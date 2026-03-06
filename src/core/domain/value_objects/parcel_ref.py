# PATH: src/core/domain/value_objects/parcel_ref.py
# DESC: ParcelRef VO; il/ilce/mahalle-koy + ada/parsel hash tekillestirme.
# SSOT: KR-013 (tarla yonetimi), KR-080 (teknik kurallar)
"""
ParcelRef value object.

Turkiye kadastro sistemindeki il/ilce/mahalle-koy/ada/parsel bilesimini
immutable olarak temsil eder. Tekil kayit kontrolu icin hash uretir.
PII icermez (konum verisi, kisisel veri degil).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class ParcelRef:
    """Immutable parsel referansi.

    * KR-013 -- Tarla kaydi tekil kontrol: il+ilce+koy+ada+parsel.
    * KR-080 -- Teknik kurallar; ayni kombinasyon tekrar edemez.

    frozen=True: olusturulduktan sonra alanlari degistirilemez.
    """

    province: str
    district: str
    village: str
    ada: str
    parsel: str

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        for field_name in ("province", "district", "village", "ada", "parsel"):
            value = getattr(self, field_name)
            if not value or not value.strip():
                raise ValueError(f"{field_name} is required and cannot be blank")
        # Normalize: strip whitespace (frozen requires object.__setattr__)
        object.__setattr__(self, "province", self.province.strip())
        object.__setattr__(self, "district", self.district.strip())
        object.__setattr__(self, "village", self.village.strip())
        object.__setattr__(self, "ada", self.ada.strip())
        object.__setattr__(self, "parsel", self.parsel.strip())

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------
    @property
    def composite_key(self) -> str:
        """Slash-separated composite key (goruntuleme / log icin)."""
        return f"{self.province}/{self.district}/{self.village}/{self.ada}/{self.parsel}"

    @property
    def unique_hash(self) -> str:
        """SHA-256 hash ile tekillik kontrolu icin deterministik deger.

        Veritabaninda UNIQUE constraint yerine veya ek kontrol olarak
        kullanilabilir.
        """
        raw = self.composite_key.lower()
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, str]:
        return {
            "province": self.province,
            "district": self.district,
            "village": self.village,
            "ada": self.ada,
            "parsel": self.parsel,
            "composite_key": self.composite_key,
            "unique_hash": self.unique_hash,
        }
