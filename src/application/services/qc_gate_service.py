# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-018: QC decisioning blocks invalid datasets from analysis.

from __future__ import annotations

import enum
from dataclasses import dataclass


class QCDecision(str, enum.Enum):
    PASS = "pass"  # noqa: S105
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class QCEvidence:
    dataset_id: str
    blur_ratio: float
    missing_band_ratio: float
    overlap_ok: bool
    notes: str | None = None
    # KR-018 v1.2.0: available_bands + beklenen band sayisi
    available_bands: tuple[str, ...] = ()
    expected_band_count: int = 4  # minimum 4 band zorunlu


class QcGateService:
    def __init__(
        self,
        *,
        blur_fail_threshold: float = 0.35,
        blur_warn_threshold: float = 0.20,
        missing_band_fail_threshold: float = 0.05,
    ) -> None:
        self._blur_fail = blur_fail_threshold
        self._blur_warn = blur_warn_threshold
        self._missing_band_fail = missing_band_fail_threshold

    def decide(self, evidence: QCEvidence, *, correlation_id: str) -> QCDecision:
        _ = correlation_id
        if not evidence.overlap_ok:
            return QCDecision.FAIL
        if evidence.missing_band_ratio > self._missing_band_fail:
            return QCDecision.FAIL
        if evidence.blur_ratio > self._blur_fail:
            return QCDecision.FAIL
        # KR-018 v1.2.0: available_bands kontrolu
        if evidence.available_bands and len(evidence.available_bands) < evidence.expected_band_count:
            return QCDecision.FAIL
        if evidence.blur_ratio > self._blur_warn:
            return QCDecision.WARN
        return QCDecision.PASS
