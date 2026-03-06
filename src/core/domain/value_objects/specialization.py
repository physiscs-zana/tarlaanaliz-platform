# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/value_objects/specialization.py
# DESC: Specialization VO; uzman uzmanlık alanları enum (KR-019).
# SSOT: KR-019 (expert portal / uzman inceleme)
"""
Specialization value object.

KR-019 kapsamında uzman uzmanlık alanlarını enum olarak temsil eder.
ExpertSpecialization VO'sunun daha hafif, enum tabanlı alternatifidir.
Entity katmanında string olarak tutulan uzmanlık alanlarının
domain seviyesinde doğrulanmasını sağlar.
"""

from __future__ import annotations

from enum import Enum


class Specialization(str, Enum):
    """KR-019 kanonik uzman uzmanlık alanları.

    * CROP_DISEASE      -- Bitki hastalıkları.
    * PEST_DETECTION    -- Zararlı böcek tespiti.
    * WEED_ANALYSIS     -- Yabancı ot analizi.
    * WATER_STRESS      -- Su stresi analizi.
    * NUTRIENT_STRESS   -- Besin stresi analizi (azot vb.).
    * GENERAL_HEALTH    -- Genel sağlık değerlendirmesi.
    * FUNGUS_DETECTION  -- Mantar tespiti.
    * THERMAL_STRESS    -- Termal stres / sulama analizi (KR-084, v1.2.0).

    SSOT'taki map layer kodlarıyla (HEALTH, WEED, DISEASE, PEST,
    FUNGUS, WATER_STRESS, N_STRESS, THERMAL_STRESS) uyumludur.
    """

    CROP_DISEASE = "CROP_DISEASE"
    PEST_DETECTION = "PEST_DETECTION"
    WEED_ANALYSIS = "WEED_ANALYSIS"
    WATER_STRESS = "WATER_STRESS"
    NUTRIENT_STRESS = "NUTRIENT_STRESS"
    GENERAL_HEALTH = "GENERAL_HEALTH"
    FUNGUS_DETECTION = "FUNGUS_DETECTION"
    THERMAL_STRESS = "THERMAL_STRESS"  # KR-084 v1.2.0


# Uzmanlık alanı -> İlişkili map layer kodları (SSOT)
SPECIALIZATION_LAYER_MAPPINGS: dict[Specialization, tuple[str, ...]] = {
    Specialization.CROP_DISEASE: ("DISEASE",),
    Specialization.PEST_DETECTION: ("PEST",),
    Specialization.WEED_ANALYSIS: ("WEED",),
    Specialization.WATER_STRESS: ("WATER_STRESS",),
    Specialization.NUTRIENT_STRESS: ("N_STRESS",),
    Specialization.GENERAL_HEALTH: ("HEALTH",),
    Specialization.FUNGUS_DETECTION: ("FUNGUS",),
    Specialization.THERMAL_STRESS: ("THERMAL_STRESS",),  # KR-084 v1.2.0
}

# Uzmanlık alanı -> Türkçe görünen ad eşlemesi
SPECIALIZATION_DISPLAY_NAMES: dict[Specialization, str] = {
    Specialization.CROP_DISEASE: "Bitki Hastalıkları",
    Specialization.PEST_DETECTION: "Zararlı Böcek Tespiti",
    Specialization.WEED_ANALYSIS: "Yabancı Ot Analizi",
    Specialization.WATER_STRESS: "Su Stresi Analizi",
    Specialization.NUTRIENT_STRESS: "Besin Stresi Analizi",
    Specialization.GENERAL_HEALTH: "Genel Sağlık Değerlendirmesi",
    Specialization.FUNGUS_DETECTION: "Mantar Tespiti",
    Specialization.THERMAL_STRESS: "Termal Stres / Sulama Analizi",  # KR-084 v1.2.0
}


def get_specialization_display_name(spec: Specialization) -> str:
    """Uzmanlık alanının Türkçe görünen adını döner."""
    return SPECIALIZATION_DISPLAY_NAMES[spec]


def get_related_layer_codes(spec: Specialization) -> tuple[str, ...]:
    """Uzmanlık alanının ilişkili map layer kodlarını döner."""
    return SPECIALIZATION_LAYER_MAPPINGS[spec]


def matches_finding_code(spec: Specialization, finding_code: str) -> bool:
    """Verilen finding_code bu uzmanlık alanıyla eşleşiyor mu?"""
    return finding_code.upper() in SPECIALIZATION_LAYER_MAPPINGS[spec]
