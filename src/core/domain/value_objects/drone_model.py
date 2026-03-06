# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/value_objects/drone_model.py
# DESC: DroneModel VO; drone model + sensor band dogrulama (KR-030, KR-034).
# KR-034: DJI Bagimsizlik Plani — Aktif Operasyon Plani, 5 onayli model (v1.2.0)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar


class DroneModelError(Exception):
    """DroneModel domain invariant ihlali."""


# KR-018: Analiz icin minimum gerekli bandlar
REQUIRED_BANDS: frozenset[str] = frozenset({"green", "red", "red_edge", "nir"})


@dataclass(frozen=True)
class DroneModel:
    """Drone modeli deger nesnesi (KR-030).

    Immutable (frozen=True); olusturulduktan sonra degistirilemez.
    Domain core'da dis dunya erisimi yoktur (IO, log yok).

    SSOT'a gore desteklenen drone/sensor kombinasyonlari (v1.2.0):
    - DJI Mavic 3M (birincil/onerilen, goreli radyometri, 4-band)
    - DJI Matrice 350 RTK + Sentera 6X (5-band + termal)
    - WingtraOne Gen II + MicaSense RedEdge-P (5-band)
    - Parrot Anafi USA + Sequoia+ (4-band)
    - AgEagle eBee X + Altum-PT (5-band + termal)

    KR-034 (v1.2.0): Artik "risk plani" degil, "aktif operasyon plani".
    DJI M3M tedarik zinciri sorunlari nedeniyle 5-band sensorler
    sisteme entegre edilmis; graceful degradation (KR-018/082) hazir.

    Invariants:
    - model_id bos olamaz.
    - manufacturer bos olamaz.
    - bands en az REQUIRED_BANDS icermeli (KR-018/KR-030).
    """

    model_id: str
    manufacturer: str
    model_name: str
    sensor: str
    bands: tuple[str, ...]
    min_gsd_cm: float
    radiometry_type: str  # "relative" | "absolute"
    phase: int = 1
    red_edge_wavelength_nm: float = 0.0  # KR-018 v1.2.0: DJI ~730nm, MicaSense/Sentera ~715-717nm

    # KR-034: 5 onayli model ID sabiti (v1.2.0 — aktif operasyon plani)
    # Phase 1: DJI_MAVIC_3M (birincil, relative, 4-band)
    # Phase 2 Senaryo A: PARROT_SEQUOIA_PLUS, DJI_M350_RTK_SENTERA_6X
    # Phase 2 Senaryo B: WINGTRAONE_GEN2, AGEAGLE_EBEE_X
    DJI_MAVIC_3M: ClassVar[str] = "DJI_MAVIC_3M"
    DJI_M350_RTK_SENTERA_6X: ClassVar[str] = "DJI_M350_RTK_SENTERA_6X"
    WINGTRAONE_GEN2: ClassVar[str] = "WINGTRAONE_GEN2"
    PARROT_SEQUOIA_PLUS: ClassVar[str] = "PARROT_SEQUOIA_PLUS"
    AGEAGLE_EBEE_X: ClassVar[str] = "AGEAGLE_EBEE_X"

    _APPROVED_MODEL_IDS: ClassVar[frozenset[str]] = frozenset(
        {
            "DJI_MAVIC_3M",
            "DJI_M350_RTK_SENTERA_6X",
            "WINGTRAONE_GEN2",
            "PARROT_SEQUOIA_PLUS",
            "AGEAGLE_EBEE_X",
        }
    )

    # Gecerli radyometri tipleri
    _VALID_RADIOMETRY: ClassVar[frozenset[str]] = frozenset({"relative", "absolute"})

    def __post_init__(self) -> None:
        if not isinstance(self.model_id, str) or not self.model_id.strip():
            raise DroneModelError("model_id bos olamaz")
        if not isinstance(self.manufacturer, str) or not self.manufacturer.strip():
            raise DroneModelError("manufacturer bos olamaz")
        if not isinstance(self.bands, tuple):
            object.__setattr__(self, "bands", tuple(self.bands))
        if self.radiometry_type not in self._VALID_RADIOMETRY:
            raise DroneModelError(
                f"Gecersiz radiometry_type: '{self.radiometry_type}'. "
                f"Gecerli degerler: {sorted(self._VALID_RADIOMETRY)}"
            )

    @property
    def band_set(self) -> frozenset[str]:
        """Band listesini frozenset olarak dondurur."""
        return frozenset(self.bands)

    def has_required_bands(self) -> bool:
        """KR-018: Minimum band gereksinimini kontrol eder."""
        return REQUIRED_BANDS.issubset(self.band_set)

    @property
    def missing_required_bands(self) -> frozenset[str]:
        """Eksik zorunlu bandlari dondurur."""
        return REQUIRED_BANDS - self.band_set

    @property
    def has_blue_band(self) -> bool:
        """KR-018 v1.2.0: Blue band mevcut mu? (5-band siniflandirma icin)."""
        return "blue" in self.band_set

    @property
    def band_class(self) -> str:
        """KR-018/KR-082 v1.2.0: Band sinifi (Graceful Degradation).

        BASIC_4BAND   : green, red, red_edge, nir
        EXTENDED_5BAND: + blue
        """
        from src.core.domain.value_objects.spectral_tier import classify_bands

        return classify_bands(self.band_set).value

    def supports_thermal(self) -> bool:
        """Termal band destegi var mi?"""
        return "thermal" in self.band_set or "lwir" in self.band_set

    @property
    def is_absolute_radiometry(self) -> bool:
        """Mutlak radyometrik kalibrasyon destegi."""
        return self.radiometry_type == "absolute"

    def is_approved(self) -> bool:
        """KR-034: Bu model onayli drone listesinde mi?"""
        return self.model_id in self._APPROVED_MODEL_IDS

    def to_dict(self) -> dict[str, Any]:
        """Serilestirme icin dict donusumu."""
        return {
            "model_id": self.model_id,
            "manufacturer": self.manufacturer,
            "model_name": self.model_name,
            "sensor": self.sensor,
            "bands": list(self.bands),
            "min_gsd_cm": self.min_gsd_cm,
            "radiometry_type": self.radiometry_type,
            "phase": self.phase,
            "red_edge_wavelength_nm": self.red_edge_wavelength_nm,
            "band_class": self.band_class,
        }

    def __str__(self) -> str:
        return f"{self.manufacturer} {self.model_name} ({self.sensor})"

    def __repr__(self) -> str:
        return f"DroneModel(model_id='{self.model_id}', manufacturer='{self.manufacturer}')"
