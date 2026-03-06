# PATH: src/core/domain/value_objects/qc_flag.py
# DESC: QCFlag VO; spesifik QC kontrol bayraklari (KR-018).
# SSOT: KR-018 (kalibrasyon hard gate), KR-082 (QC gate)
"""
QCFlag value object.

Kalite kontrol surecinde tespit edilen spesifik sorunlari
(blur, overexposure, missing_bands vb.) temsil eder.
KR-018 hard gate: calibrated/QC kaniti olmadan AnalysisJob baslatilamaz.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class QCFlagType(str, Enum):
    """KR-018 QC kontrol bayrak turleri.

    Her bayrak, goruntu/veri kalitesine yonelik spesifik bir sorunu temsil eder.
    """

    BLUR = "BLUR"
    OVEREXPOSURE = "OVEREXPOSURE"
    UNDEREXPOSURE = "UNDEREXPOSURE"
    MISSING_BANDS = "MISSING_BANDS"
    GEOMETRIC_DISTORTION = "GEOMETRIC_DISTORTION"
    CLOUD_COVER = "CLOUD_COVER"
    SHADOW = "SHADOW"
    NOISE = "NOISE"
    VIGNETTING = "VIGNETTING"
    BAND_MISALIGNMENT = "BAND_MISALIGNMENT"


class QCFlagSeverity(str, Enum):
    """Bayrak ciddiyet seviyesi."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class QCFlag:
    """Immutable QC kontrol bayragi.

    * KR-018 -- Kalibrasyon hard gate; QC kaniti olmadan islem baslatilamaz.
    * KR-082 -- QC gate mekanizmasi.

    frozen=True: olusturulduktan sonra alanlari degistirilemez.
    """

    flag_type: QCFlagType
    severity: QCFlagSeverity
    message: Optional[str] = None
    threshold: Optional[float] = None  # Esik degeri (varsa)
    actual_value: Optional[float] = None  # Olculen deger (varsa)

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if not isinstance(self.flag_type, QCFlagType):
            raise TypeError(f"flag_type must be QCFlagType, got {type(self.flag_type).__name__}")
        if not isinstance(self.severity, QCFlagSeverity):
            raise TypeError(f"severity must be QCFlagSeverity, got {type(self.severity).__name__}")
        if self.threshold is not None and self.threshold < 0:
            raise ValueError("threshold cannot be negative")
        if self.actual_value is not None and self.actual_value < 0:
            raise ValueError("actual_value cannot be negative")

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------
    @property
    def is_blocking(self) -> bool:
        """Bu bayrak analiz baslatmayi engelleyecek kadar ciddi mi?

        KR-018: CRITICAL severity her zaman engelleyicidir.
        """
        return self.severity == QCFlagSeverity.CRITICAL

    @property
    def exceeds_threshold(self) -> bool:
        """Olculen deger esik degerini asiyor mu?"""
        if self.threshold is None or self.actual_value is None:
            return False
        return self.actual_value > self.threshold

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "flag_type": self.flag_type.value,
            "severity": self.severity.value,
        }
        if self.message is not None:
            result["message"] = self.message
        if self.threshold is not None:
            result["threshold"] = self.threshold
        if self.actual_value is not None:
            result["actual_value"] = self.actual_value
        return result
