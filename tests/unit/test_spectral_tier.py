# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""SpectralTier VO + Graceful Degradation testleri (KR-018/KR-082 v1.2.0)."""

from __future__ import annotations

import pytest

from src.core.domain.value_objects.spectral_tier import (
    CORE_INDICES,
    EXTENDED_INDICES,
    THERMAL_INDICES,
    BandClass,
    ReportTier,
    SpectralTier,
    classify_bands,
    derive_available_indices,
    derive_enabled_pipelines,
    determine_report_tier,
    has_thermal_capability,
)


# ---- classify_bands ----

def test_classify_bands_basic_4band() -> None:
    bands = frozenset({"green", "red", "red_edge", "nir"})
    assert classify_bands(bands) == BandClass.BASIC_4BAND


def test_classify_bands_extended_5band() -> None:
    bands = frozenset({"blue", "green", "red", "red_edge", "nir"})
    assert classify_bands(bands) == BandClass.EXTENDED_5BAND


def test_classify_bands_extended_with_thermal() -> None:
    bands = frozenset({"blue", "green", "red", "red_edge", "nir", "thermal"})
    assert classify_bands(bands) == BandClass.EXTENDED_5BAND


def test_classify_bands_missing_required_raises() -> None:
    bands = frozenset({"green", "red"})
    with pytest.raises(ValueError, match="Minimum band"):
        classify_bands(bands)


# ---- has_thermal_capability ----

def test_has_thermal_true() -> None:
    assert has_thermal_capability(frozenset({"green", "red", "red_edge", "nir", "thermal"}))


def test_has_thermal_lwir() -> None:
    assert has_thermal_capability(frozenset({"green", "red", "red_edge", "nir", "lwir"}))


def test_has_thermal_false() -> None:
    assert not has_thermal_capability(frozenset({"green", "red", "red_edge", "nir"}))


# ---- derive_available_indices ----

def test_derive_indices_basic() -> None:
    indices = derive_available_indices(BandClass.BASIC_4BAND)
    assert set(indices) == set(CORE_INDICES)


def test_derive_indices_extended() -> None:
    indices = derive_available_indices(BandClass.EXTENDED_5BAND)
    assert set(CORE_INDICES).issubset(set(indices))
    assert set(EXTENDED_INDICES).issubset(set(indices))


def test_derive_indices_with_thermal() -> None:
    indices = derive_available_indices(BandClass.EXTENDED_5BAND, has_thermal=True)
    assert set(THERMAL_INDICES).issubset(set(indices))


# ---- derive_enabled_pipelines ----

def test_derive_pipelines_basic() -> None:
    pipes = derive_enabled_pipelines(BandClass.BASIC_4BAND)
    assert pipes == ("core_multispectral",)


def test_derive_pipelines_extended() -> None:
    pipes = derive_enabled_pipelines(BandClass.EXTENDED_5BAND)
    assert "core_multispectral" in pipes
    assert "extended_multispectral" in pipes


def test_derive_pipelines_with_thermal() -> None:
    pipes = derive_enabled_pipelines(BandClass.EXTENDED_5BAND, has_thermal=True)
    assert "thermal_analysis" in pipes


def test_derive_pipelines_without_thermal() -> None:
    pipes = derive_enabled_pipelines(BandClass.EXTENDED_5BAND, has_thermal=False)
    assert "thermal_analysis" not in pipes


# ---- determine_report_tier ----

def test_report_tier_temel() -> None:
    assert determine_report_tier(BandClass.BASIC_4BAND) == ReportTier.TEMEL


def test_report_tier_genisletilmis() -> None:
    assert determine_report_tier(BandClass.EXTENDED_5BAND) == ReportTier.GENISLETILMIS


def test_report_tier_kapsamli() -> None:
    assert determine_report_tier(BandClass.EXTENDED_5BAND, has_thermal=True) == ReportTier.KAPSAMLI


# ---- SpectralTier.from_bands ----

def test_spectral_tier_from_bands_basic() -> None:
    tier = SpectralTier.from_bands(frozenset({"green", "red", "red_edge", "nir"}))
    assert tier.band_class == BandClass.BASIC_4BAND
    assert tier.has_thermal is False
    assert tier.report_tier == ReportTier.TEMEL
    assert "core_multispectral" in tier.enabled_pipelines


def test_spectral_tier_from_bands_full() -> None:
    tier = SpectralTier.from_bands(frozenset({"blue", "green", "red", "red_edge", "nir", "thermal"}))
    assert tier.band_class == BandClass.EXTENDED_5BAND
    assert tier.has_thermal is True
    assert tier.report_tier == ReportTier.KAPSAMLI
    assert "thermal_analysis" in tier.enabled_pipelines
    assert "CWSI" in tier.available_indices


def test_spectral_tier_to_dict() -> None:
    tier = SpectralTier.from_bands(frozenset({"green", "red", "red_edge", "nir"}))
    d = tier.to_dict()
    assert d["band_class"] == "BASIC_4BAND"
    assert d["report_tier"] == "TEMEL"
    assert isinstance(d["available_bands"], list)
