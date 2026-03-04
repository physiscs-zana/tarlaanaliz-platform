# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""DroneModel VO v1.2.0 testleri: DJI M350, band_class, red_edge_wavelength."""

from __future__ import annotations

from src.core.domain.value_objects.drone_model import DroneModel


def _mavic_3m() -> DroneModel:
    return DroneModel(
        model_id="DJI_MAVIC_3M",
        manufacturer="DJI",
        model_name="Mavic 3 Multispectral",
        sensor="Integrated MS",
        bands=("green", "red", "red_edge", "nir"),
        min_gsd_cm=5.0,
        radiometry_type="relative",
        phase=1,
        red_edge_wavelength_nm=730.0,
    )


def _m350() -> DroneModel:
    return DroneModel(
        model_id="DJI_M350_RTK_SENTERA_6X",
        manufacturer="DJI",
        model_name="Matrice 350 RTK",
        sensor="Sentera 6X",
        bands=("blue", "green", "red", "red_edge", "nir", "thermal"),
        min_gsd_cm=3.0,
        radiometry_type="absolute",
        phase=2,
        red_edge_wavelength_nm=717.0,
    )


def _ebee_x() -> DroneModel:
    return DroneModel(
        model_id="AGEAGLE_EBEE_X",
        manufacturer="AgEagle",
        model_name="eBee X",
        sensor="Altum-PT",
        bands=("blue", "green", "red", "red_edge", "nir", "thermal"),
        min_gsd_cm=2.4,
        radiometry_type="absolute",
        phase=2,
        red_edge_wavelength_nm=717.0,
    )


# ---- Approved models (v1.2.0: 5 model) ----

def test_dji_m350_approved() -> None:
    m = _m350()
    assert m.is_approved()
    assert m.model_id == DroneModel.DJI_M350_RTK_SENTERA_6X


def test_mavic_3m_approved() -> None:
    assert _mavic_3m().is_approved()


def test_all_five_approved() -> None:
    ids = {"DJI_MAVIC_3M", "DJI_M350_RTK_SENTERA_6X", "WINGTRAONE_GEN2", "PARROT_SEQUOIA_PLUS", "AGEAGLE_EBEE_X"}
    assert ids == DroneModel._APPROVED_MODEL_IDS


# ---- band_class property ----

def test_band_class_basic() -> None:
    assert _mavic_3m().band_class == "BASIC_4BAND"


def test_band_class_extended() -> None:
    assert _m350().band_class == "EXTENDED_5BAND"


# ---- has_blue_band ----

def test_has_blue_band_false() -> None:
    assert not _mavic_3m().has_blue_band


def test_has_blue_band_true() -> None:
    assert _m350().has_blue_band


# ---- supports_thermal ----

def test_supports_thermal_false() -> None:
    assert not _mavic_3m().supports_thermal()


def test_supports_thermal_true() -> None:
    assert _m350().supports_thermal()
    assert _ebee_x().supports_thermal()


# ---- red_edge_wavelength_nm ----

def test_red_edge_wavelength_dji() -> None:
    assert _mavic_3m().red_edge_wavelength_nm == 730.0


def test_red_edge_wavelength_sentera() -> None:
    assert _m350().red_edge_wavelength_nm == 717.0


# ---- to_dict includes v1.2.0 fields ----

def test_to_dict_v120_fields() -> None:
    d = _m350().to_dict()
    assert "red_edge_wavelength_nm" in d
    assert "band_class" in d
    assert d["band_class"] == "EXTENDED_5BAND"
