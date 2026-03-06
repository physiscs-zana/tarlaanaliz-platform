# PATH: src/core/domain/value_objects/expert_specialization.py
# DESC: ExpertSpecialization VO; uzman uzmanlık alanları (KR-019).

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar


class ExpertSpecializationError(Exception):
    """ExpertSpecialization domain invariant ihlali."""


@dataclass(frozen=True)
class ExpertSpecialization:
    """Uzman uzmanlık alanı değer nesnesi (KR-019).

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    KR-019 kapsamında uzmanlar belirli alanlarda uzmandır:
    - CROP_DISEASE: Bitki hastalıkları
    - PEST_DETECTION: Zararlı böcek tespiti
    - WEED_ANALYSIS: Yabancı ot analizi
    - WATER_STRESS: Su stresi analizi
    - NUTRIENT_STRESS: Besin stresi (azot vb.)
    - GENERAL_HEALTH: Genel sağlık değerlendirmesi
    - FUNGUS_DETECTION: Mantar tespiti

    Bu alanlar SSOT'taki map layer kodlarıyla (HEALTH, WEED, DISEASE, PEST,
    FUNGUS, WATER_STRESS, N_STRESS) uyumludur.

    Invariants:
    - code, tanımlı geçerli uzmanlık alanlarından biri olmalıdır.
    """

    code: str

    # Sabit uzmanlık alanı kodları
    CROP_DISEASE: ClassVar[str] = "CROP_DISEASE"
    PEST_DETECTION: ClassVar[str] = "PEST_DETECTION"
    WEED_ANALYSIS: ClassVar[str] = "WEED_ANALYSIS"
    WATER_STRESS: ClassVar[str] = "WATER_STRESS"
    NUTRIENT_STRESS: ClassVar[str] = "NUTRIENT_STRESS"
    GENERAL_HEALTH: ClassVar[str] = "GENERAL_HEALTH"
    FUNGUS_DETECTION: ClassVar[str] = "FUNGUS_DETECTION"

    _VALID_CODES: ClassVar[frozenset[str]] = frozenset(
        {
            "CROP_DISEASE",
            "PEST_DETECTION",
            "WEED_ANALYSIS",
            "WATER_STRESS",
            "NUTRIENT_STRESS",
            "GENERAL_HEALTH",
            "FUNGUS_DETECTION",
        }
    )

    # Uzmanlık alanı -> Türkçe görünen ad eşlemesi
    _DISPLAY_NAMES: ClassVar[dict[str, str]] = {
        "CROP_DISEASE": "Bitki Hastalıkları",
        "PEST_DETECTION": "Zararlı Böcek Tespiti",
        "WEED_ANALYSIS": "Yabancı Ot Analizi",
        "WATER_STRESS": "Su Stresi Analizi",
        "NUTRIENT_STRESS": "Besin Stresi Analizi",
        "GENERAL_HEALTH": "Genel Sağlık Değerlendirmesi",
        "FUNGUS_DETECTION": "Mantar Tespiti",
    }

    # Uzmanlık alanı -> İlişkili map layer kodları (SSOT)
    _LAYER_MAPPINGS: ClassVar[dict[str, tuple[str, ...]]] = {
        "CROP_DISEASE": ("DISEASE",),
        "PEST_DETECTION": ("PEST",),
        "WEED_ANALYSIS": ("WEED",),
        "WATER_STRESS": ("WATER_STRESS",),
        "NUTRIENT_STRESS": ("N_STRESS",),
        "GENERAL_HEALTH": ("HEALTH",),
        "FUNGUS_DETECTION": ("FUNGUS",),
    }

    def __post_init__(self) -> None:
        if not isinstance(self.code, str):
            raise ExpertSpecializationError(f"code str olmalıdır, alınan tip: {type(self.code).__name__}")
        normalized = self.code.strip().upper()
        if normalized != self.code:
            object.__setattr__(self, "code", normalized)
        if self.code not in self._VALID_CODES:
            raise ExpertSpecializationError(
                f"Geçersiz uzmanlık alanı: '{self.code}'. Geçerli değerler: {sorted(self._VALID_CODES)}"
            )

    @property
    def display_name(self) -> str:
        """Türkçe görünen ad."""
        return self._DISPLAY_NAMES[self.code]

    @property
    def related_layer_codes(self) -> tuple[str, ...]:
        """İlişkili map layer kodları (SSOT finding types)."""
        return self._LAYER_MAPPINGS[self.code]

    def matches_finding_code(self, finding_code: str) -> bool:
        """Verilen finding_code bu uzmanlık alanıyla eşleşiyor mu?"""
        return finding_code.upper() in self.related_layer_codes

    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return {
            "code": self.code,
            "display_name": self.display_name,
            "related_layer_codes": list(self.related_layer_codes),
        }

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return f"ExpertSpecialization(code='{self.code}')"
