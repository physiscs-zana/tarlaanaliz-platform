# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/value_objects/spectral_tier.py
# DESC: SpectralTier VO; KR-018/KR-082 Graceful Degradation band siniflandirma.
# KR-018/KR-082: Spektral kapasite algilama + 3 katmanli pipeline yonlendirme.
# ADR-002: Graceful Degradation modeli (v1.2.0).
"""
SpectralTier value object.

KR-018/KR-082 (v1.2.0): Drone sensor bandlarina gore 3 katmanli
spektral siniflandirma ve pipeline yonlendirme.

Band Siniflandirma:
  BASIC_4BAND   : green, red, red_edge, nir → NDVI, NDRE, GNDVI
  EXTENDED_5BAND: + blue → EVI, SAVI, chlorophyll-a (Sentinel-2 uyumlu)
  (THERMAL opsiyonel herhangi bir sinifa eklenebilir)

Graceful Degradation:
  Worker, intake_manifest.available_bands[] icerigine gore
  pipeline secimini dinamik olarak yapar. 5-band verisi yoksa
  4-band pipeline calisir; termal veri yoksa termal pipeline atlanir.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.core.domain.value_objects.drone_model import REQUIRED_BANDS


class BandClass(str, Enum):
    """KR-018/KR-082 kanonik band siniflari."""

    BASIC_4BAND = "BASIC_4BAND"
    EXTENDED_5BAND = "EXTENDED_5BAND"


class ReportTier(str, Enum):
    """KR-023 rapor katmanlari."""

    TEMEL = "TEMEL"
    GENISLETILMIS = "GENISLETILMIS"
    KAPSAMLI = "KAPSAMLI"


# ---- Kanonik indeks gruplari ----

CORE_INDICES: tuple[str, ...] = ("NDVI", "NDRE", "GNDVI")

EXTENDED_INDICES: tuple[str, ...] = ("EVI", "SAVI", "CHLOROPHYLL_A")

THERMAL_INDICES: tuple[str, ...] = ("CWSI", "CANOPY_TEMP", "CANOPY_SOIL_DELTA_T")

# ---- Pipeline tanimlari ----

PIPELINE_CORE = "core_multispectral"
PIPELINE_EXTENDED = "extended_multispectral"
PIPELINE_THERMAL = "thermal_analysis"

# ---- Blue band tespiti icin ----

BLUE_BAND = "blue"
THERMAL_BANDS: frozenset[str] = frozenset({"thermal", "lwir"})


def classify_bands(bands: frozenset[str]) -> BandClass:
    """Band listesinden BandClass sinifini belirler.

    Args:
        bands: Mevcut band isimleri (kucuk harf).

    Returns:
        BandClass: BASIC_4BAND veya EXTENDED_5BAND.

    Raises:
        ValueError: Minimum 4 band (REQUIRED_BANDS) yoksa.
    """
    if not REQUIRED_BANDS.issubset(bands):
        missing = REQUIRED_BANDS - bands
        raise ValueError(f"Minimum band gereksinimi karsilanmiyor. Eksik: {sorted(missing)}")

    if BLUE_BAND in bands:
        return BandClass.EXTENDED_5BAND
    return BandClass.BASIC_4BAND


def has_thermal_capability(bands: frozenset[str]) -> bool:
    """Band listesinde termal band var mi?"""
    return bool(bands & THERMAL_BANDS)


def derive_available_indices(band_class: BandClass, has_thermal: bool = False) -> tuple[str, ...]:
    """Band sinifina gore kullanilabilir indeksleri dondurur.

    Args:
        band_class: BASIC_4BAND veya EXTENDED_5BAND.
        has_thermal: Termal band mevcut mu?

    Returns:
        Kullanilabilir indeks isimleri.
    """
    indices: list[str] = list(CORE_INDICES)

    if band_class == BandClass.EXTENDED_5BAND:
        indices.extend(EXTENDED_INDICES)

    if has_thermal:
        indices.extend(THERMAL_INDICES)

    return tuple(indices)


def derive_enabled_pipelines(band_class: BandClass, has_thermal: bool = False) -> tuple[str, ...]:
    """Band sinifina gore etkinlestirilecek pipeline'lari dondurur.

    Args:
        band_class: BASIC_4BAND veya EXTENDED_5BAND.
        has_thermal: Termal band mevcut mu?

    Returns:
        Etkin pipeline isimleri.
    """
    pipelines: list[str] = [PIPELINE_CORE]

    if band_class == BandClass.EXTENDED_5BAND:
        pipelines.append(PIPELINE_EXTENDED)

    if has_thermal:
        pipelines.append(PIPELINE_THERMAL)

    return tuple(pipelines)


def determine_report_tier(band_class: BandClass, has_thermal: bool = False) -> ReportTier:
    """Band sinifina gore rapor katmanini belirler (KR-023).

    TEMEL         : 4-band (BASIC_4BAND, termal yok)
    GENISLETILMIS : 5-band (EXTENDED_5BAND, termal yok)
    KAPSAMLI      : 5-band + termal
    """
    if band_class == BandClass.EXTENDED_5BAND and has_thermal:
        return ReportTier.KAPSAMLI
    if band_class == BandClass.EXTENDED_5BAND:
        return ReportTier.GENISLETILMIS
    return ReportTier.TEMEL


@dataclass(frozen=True)
class SpectralTier:
    """Spektral kapasite ozeti deger nesnesi.

    Immutable (frozen=True); olusturulduktan sonra degistirilemez.
    Domain core'da dis dunya erisimi yoktur (IO, log yok).

    KR-018/KR-082: Graceful degradation pipeline yonlendirme bilgisi.
    """

    band_class: BandClass
    has_thermal: bool
    available_bands: tuple[str, ...]
    available_indices: tuple[str, ...]
    enabled_pipelines: tuple[str, ...]
    report_tier: ReportTier

    def to_dict(self) -> dict[str, Any]:
        return {
            "band_class": self.band_class.value,
            "has_thermal": self.has_thermal,
            "available_bands": list(self.available_bands),
            "available_indices": list(self.available_indices),
            "enabled_pipelines": list(self.enabled_pipelines),
            "report_tier": self.report_tier.value,
        }

    @classmethod
    def from_bands(cls, bands: frozenset[str]) -> SpectralTier:
        """Band listesinden SpectralTier olusturur.

        Args:
            bands: Mevcut band isimleri (kucuk harf).

        Returns:
            SpectralTier: Hesaplanmis spektral kapasite ozeti.
        """
        band_class = classify_bands(bands)
        thermal = has_thermal_capability(bands)
        return cls(
            band_class=band_class,
            has_thermal=thermal,
            available_bands=tuple(sorted(bands)),
            available_indices=derive_available_indices(band_class, thermal),
            enabled_pipelines=derive_enabled_pipelines(band_class, thermal),
            report_tier=determine_report_tier(band_class, thermal),
        )

    def __repr__(self) -> str:
        return (
            f"SpectralTier(band_class={self.band_class.value}, "
            f"has_thermal={self.has_thermal}, "
            f"report_tier={self.report_tier.value})"
        )
