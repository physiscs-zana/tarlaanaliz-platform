# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/services/band_compliance_checker.py
# DESC: Drone model + sensor band uyumluluk + Graceful Degradation servisi (KR-030/KR-018/KR-082).

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.domain.value_objects.drone_model import REQUIRED_BANDS, DroneModel
from src.core.domain.value_objects.spectral_tier import (
    BandClass,
    ReportTier,
    classify_bands,
    derive_available_indices,
    derive_enabled_pipelines,
    determine_report_tier,
    has_thermal_capability,
)


class BandComplianceError(Exception):
    """Band compliance domain invariant ihlali."""


@dataclass(frozen=True)
class BandComplianceResult:
    """Band uyumluluk kontrolu sonucu (v1.2.0 Graceful Degradation).

    compliant: True ise drone analiz icin uygundur.
    KR-030: Kayitli olmayan drone modeli sisteme kabul edilmez.
    KR-018: Minimum band gereksinimi karsilanmalidir.
    KR-018/KR-082 v1.2.0: band_class, available_indices, enabled_pipelines, report_tier.
    """

    compliant: bool
    model_id: str
    missing_bands: frozenset[str]
    message: str
    radiometry_warning: bool = False
    # v1.2.0 Graceful Degradation alanlari
    band_class: str = ""
    available_indices: tuple[str, ...] = ()
    enabled_pipelines: tuple[str, ...] = ()
    report_tier: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "compliant": self.compliant,
            "model_id": self.model_id,
            "missing_bands": sorted(self.missing_bands),
            "message": self.message,
            "radiometry_warning": self.radiometry_warning,
            "band_class": self.band_class,
            "available_indices": list(self.available_indices),
            "enabled_pipelines": list(self.enabled_pipelines),
            "report_tier": self.report_tier,
        }


class BandComplianceChecker:
    """Drone model + sensor band uyumluluk kontrol servisi.

    Tek entity'ye sigmayan saf is mantigi; policy ve hesaplamalar.

    KR-030: Baslangiçta yalnizca drone_registry.yaml'a kayitli modeller kabul edilir.
    KR-018: Analiz icin minimum band gereksinimi (green, red, red_edge, nir).
    KR-018/KR-082 v1.2.0: Graceful Degradation — band sinifi algilama + pipeline yonlendirme.
    KR-034: Aktif operasyon plani kapsaminda alternatif modeller de desteklenir.

    Domain invariants:
    - Drone modeli izin verilen modeller arasinda olmalidir.
    - Minimum bandlar (green, red, red_edge, nir) mevcut olmalidir.
    - Goreli radyometri (relative) kullanan modeller icin uyari uretilir.
    - v1.2.0: Basarili kontrolde band_class, available_indices, enabled_pipelines, report_tier hesaplanir.
    """

    def __init__(self, allowed_model_ids: frozenset[str] | None = None) -> None:
        """
        Args:
            allowed_model_ids: Izin verilen drone model ID'leri.
                None ise model ID kontrolu yapilmaz (yalnizca band kontrolu).
        """
        self._allowed_model_ids = allowed_model_ids

    def check(self, drone: DroneModel) -> BandComplianceResult:
        """Drone modelinin band uyumlulugunu kontrol eder.

        Args:
            drone: Kontrol edilecek DroneModel deger nesnesi.

        Returns:
            BandComplianceResult: Uyumluluk sonucu (v1.2.0: Graceful Degradation bilgisi dahil).
        """
        # 1. Model ID kontrolu (eger izin listesi verilmisse)
        if self._allowed_model_ids is not None and drone.model_id not in self._allowed_model_ids:
            return BandComplianceResult(
                compliant=False,
                model_id=drone.model_id,
                missing_bands=frozenset(),
                message=(
                    f"Drone modeli '{drone.model_id}' izin verilen modeller "
                    f"arasinda degil. Kayitli modeller: {sorted(self._allowed_model_ids)}"
                ),
            )

        # 2. Band gereksinimi kontrolu (KR-018)
        missing = REQUIRED_BANDS - drone.band_set
        if missing:
            return BandComplianceResult(
                compliant=False,
                model_id=drone.model_id,
                missing_bands=missing,
                message=f"Eksik zorunlu bandlar: {sorted(missing)}. KR-018 hard gate.",
            )

        # 3. Radyometri tipi uyarisi
        radiometry_warning = not drone.is_absolute_radiometry
        message = "Band uyumlulugu basarili."
        if radiometry_warning:
            message += (
                " Uyari: Goreli radyometri (relative) kullaniliyor. "
                "Zaman serisi tutarliligi icin mutlak radyometri onerilir (KR-018)."
            )

        # 4. v1.2.0 Graceful Degradation: band sinifi + pipeline yonlendirme
        band_cls = classify_bands(drone.band_set)
        thermal = has_thermal_capability(drone.band_set)
        indices = derive_available_indices(band_cls, thermal)
        pipelines = derive_enabled_pipelines(band_cls, thermal)
        tier = determine_report_tier(band_cls, thermal)

        return BandComplianceResult(
            compliant=True,
            model_id=drone.model_id,
            missing_bands=frozenset(),
            message=message,
            radiometry_warning=radiometry_warning,
            band_class=band_cls.value,
            available_indices=indices,
            enabled_pipelines=pipelines,
            report_tier=tier.value,
        )
