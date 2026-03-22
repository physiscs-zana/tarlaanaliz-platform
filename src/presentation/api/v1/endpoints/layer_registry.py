# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-002: Harita katman tanimlari — renk, desen, oncelik.
# KR-064: Layer Registry kanonik kaynak.
"""Layer registry endpoint — KR-002 harita katman renk/desen bilgileri."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/layers", tags=["layers"])

# KR-002: Kanonik katman tanimlari (SSOT v1.2.0)
_LAYER_REGISTRY: list[dict[str, object]] = [
    {
        "code": "HEALTH",
        "name_tr": "Saglik",
        "name_en": "Health",
        "color": "#22c55e",
        "pattern": "solid",
        "priority": 1,
        "requires_bands": ["Green", "Red", "RedEdge", "NIR"],
    },
    {
        "code": "DISEASE",
        "name_tr": "Hastalik",
        "name_en": "Disease",
        "color": "#f97316",
        "pattern": "solid",
        "priority": 2,
        "requires_bands": ["Green", "Red", "RedEdge", "NIR"],
    },
    {
        "code": "PEST",
        "name_tr": "Zararli Bocek",
        "name_en": "Pest",
        "color": "#ef4444",
        "pattern": "solid",
        "priority": 3,
        "requires_bands": ["Green", "Red", "RedEdge", "NIR"],
    },
    {
        "code": "FUNGUS",
        "name_tr": "Mantar",
        "name_en": "Fungus",
        "color": "#a855f7",
        "pattern": "solid",
        "priority": 4,
        "requires_bands": ["Green", "Red", "RedEdge", "NIR"],
    },
    {
        "code": "WEED",
        "name_tr": "Yabanci Ot",
        "name_en": "Weed",
        "color": "#eab308",
        "pattern": "dotted",
        "priority": 5,
        "requires_bands": ["Green", "Red", "RedEdge", "NIR"],
    },
    {
        "code": "WATER_STRESS",
        "name_tr": "Su Stresi",
        "name_en": "Water Stress",
        "color": "#3b82f6",
        "pattern": "water_drop",
        "priority": 6,
        "requires_bands": ["Green", "Red", "RedEdge", "NIR"],
    },
    {
        "code": "NITROGEN_STRESS",
        "name_tr": "Azot Stresi",
        "name_en": "Nitrogen Stress",
        "color": "#94a3b8",
        "pattern": "cross_hatched",
        "priority": 7,
        "requires_bands": ["Green", "Red", "RedEdge", "NIR"],
    },
    {
        "code": "THERMAL_STRESS",
        "name_tr": "Termal Stres",
        "name_en": "Thermal Stress",
        "color": "#dc2626",
        "pattern": "heatmap",
        "priority": 8,
        "requires_bands": ["LWIR"],
    },
]


@router.get("")
def get_layer_registry() -> dict[str, object]:
    """KR-002 + KR-064: Harita katman tanimlari (renk, desen, oncelik, bant gereksinimleri)."""
    return {"layers": _LAYER_REGISTRY}


__all__ = ["router"]
