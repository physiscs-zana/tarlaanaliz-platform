# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""BandComplianceChecker v1.2.0 testleri: Graceful Degradation + katmanli rapor."""

from __future__ import annotations

from src.core.domain.services.band_compliance_checker import BandComplianceChecker
from src.core.domain.value_objects.drone_model import DroneModel


def _drone_4band() -> DroneModel:
    return DroneModel(
        model_id="DJI_MAVIC_3M",
        manufacturer="DJI",
        model_name="Mavic 3M",
        sensor="MS",
        bands=("green", "red", "red_edge", "nir"),
        min_gsd_cm=5.0,
        radiometry_type="relative",
    )


def _drone_5band() -> DroneModel:
    return DroneModel(
        model_id="WINGTRAONE_GEN2",
        manufacturer="Wingtra",
        model_name="Gen II",
        sensor="MicaSense RedEdge-P",
        bands=("blue", "green", "red", "red_edge", "nir"),
        min_gsd_cm=2.9,
        radiometry_type="absolute",
    )


def _drone_5band_thermal() -> DroneModel:
    return DroneModel(
        model_id="AGEAGLE_EBEE_X",
        manufacturer="AgEagle",
        model_name="eBee X",
        sensor="Altum-PT",
        bands=("blue", "green", "red", "red_edge", "nir", "thermal"),
        min_gsd_cm=2.4,
        radiometry_type="absolute",
    )


# ---- Graceful Degradation band class ----

def test_graceful_degradation_4band() -> None:
    checker = BandComplianceChecker()
    result = checker.check(_drone_4band())
    assert result.compliant
    assert result.band_class == "BASIC_4BAND"
    assert result.report_tier == "TEMEL"
    assert "core_multispectral" in result.enabled_pipelines


def test_graceful_degradation_5band() -> None:
    checker = BandComplianceChecker()
    result = checker.check(_drone_5band())
    assert result.compliant
    assert result.band_class == "EXTENDED_5BAND"
    assert result.report_tier == "GENISLETILMIS"
    assert "extended_multispectral" in result.enabled_pipelines
    assert "thermal_analysis" not in result.enabled_pipelines


def test_graceful_degradation_5band_thermal() -> None:
    checker = BandComplianceChecker()
    result = checker.check(_drone_5band_thermal())
    assert result.compliant
    assert result.band_class == "EXTENDED_5BAND"
    assert result.report_tier == "KAPSAMLI"
    assert "thermal_analysis" in result.enabled_pipelines
    assert "CWSI" in result.available_indices


# ---- Report tier ----

def test_report_tier_temel() -> None:
    checker = BandComplianceChecker()
    result = checker.check(_drone_4band())
    assert result.report_tier == "TEMEL"


def test_report_tier_genisletilmis() -> None:
    checker = BandComplianceChecker()
    result = checker.check(_drone_5band())
    assert result.report_tier == "GENISLETILMIS"


def test_report_tier_kapsamli() -> None:
    checker = BandComplianceChecker()
    result = checker.check(_drone_5band_thermal())
    assert result.report_tier == "KAPSAMLI"


# ---- Available indices per tier ----

def test_indices_4band_core_only() -> None:
    checker = BandComplianceChecker()
    result = checker.check(_drone_4band())
    assert "NDVI" in result.available_indices
    assert "NDRE" in result.available_indices
    assert "GNDVI" in result.available_indices
    assert "EVI" not in result.available_indices


def test_indices_5band_includes_extended() -> None:
    checker = BandComplianceChecker()
    result = checker.check(_drone_5band())
    assert "EVI" in result.available_indices
    assert "SAVI" in result.available_indices
    assert "CHLOROPHYLL_A" in result.available_indices


def test_indices_thermal_includes_cwsi() -> None:
    checker = BandComplianceChecker()
    result = checker.check(_drone_5band_thermal())
    assert "CWSI" in result.available_indices
    assert "CANOPY_TEMP" in result.available_indices
    assert "CANOPY_SOIL_DELTA_T" in result.available_indices


# ---- to_dict includes v1.2.0 fields ----

def test_to_dict_v120() -> None:
    checker = BandComplianceChecker()
    result = checker.check(_drone_5band_thermal())
    d = result.to_dict()
    assert "band_class" in d
    assert "available_indices" in d
    assert "enabled_pipelines" in d
    assert "report_tier" in d
