# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-018: Calibration and QC evidence is a hard gate before analysis start.
"""
Amac: KR-018 'Tam Radyometrik Kalibrasyon' hard gate'i.
Sorumluluk: Use-case orkestrasyonu; domain service + ports birlesimi; policy enforcement.
Notlar/SSOT: KR-018 hard gate: calibrated/QC kaniti olmadan AnalysisJob baslatilmamalidir.
KR-018 v1.2.0: available_bands kontrolu eklendi (minimum 4 band zorunlu).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

# KR-018 v1.2.0: Minimum band sayisi
_MIN_REQUIRED_BANDS = 4


@dataclass(frozen=True, slots=True)
class CalibrationEvidence:
    dataset_id: str
    is_calibrated: bool
    qc_status: str
    proof_uri: str | None = None
    available_bands: tuple[str, ...] = ()  # KR-018 v1.2.0


class CalibrationEvidenceStore(Protocol):
    def get_latest_for_dataset(self, dataset_id: str) -> CalibrationEvidence | None: ...


class CalibrationGateError(RuntimeError):
    pass


class CalibrationGateService:
    def __init__(self, store: CalibrationEvidenceStore) -> None:
        self._store = store

    def require_calibrated_and_qc_ok(self, *, dataset_id: str, correlation_id: str) -> CalibrationEvidence:
        _ = correlation_id
        evidence = self._store.get_latest_for_dataset(dataset_id)
        if evidence is None:
            raise CalibrationGateError("KR-018: calibration/QC evidence not found")
        if not evidence.is_calibrated:
            raise CalibrationGateError("KR-018: dataset is not calibrated")
        if evidence.qc_status not in {"pass", "warn"}:
            raise CalibrationGateError(f"KR-018: QC status not acceptable ({evidence.qc_status})")
        # KR-018 v1.2.0: available_bands minimum 4 band kontrolu
        if len(evidence.available_bands) < _MIN_REQUIRED_BANDS:
            raise CalibrationGateError(
                f"KR-018 v1.2.0: available_bands minimum {_MIN_REQUIRED_BANDS} band "
                f"icermelidir, mevcut: {len(evidence.available_bands)}"
            )
        return evidence
