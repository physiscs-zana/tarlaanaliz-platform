# PATH: src/core/domain/entities/calibration_record.py
# DESC: CalibrationRecord; KR-018 radyometrik kalibrasyon kaniti.
# SSOT: KR-018/KR-082 (tam radyometrik kalibrasyon zorunlulugu)
"""
CalibrationRecord domain entity.

Calibrated Dataset uretilmeden AnalysisJob baslatilamaz (KR-018 hard gate).
Istasyon akisi: M1 (Offline, Pix4Dfields kalibrasyon) -> M2 (Dispatch, mTLS upload).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class CalibrationStatus(str, Enum):
    PENDING = "PENDING"
    CALIBRATED = "CALIBRATED"
    FAILED = "FAILED"


@dataclass
class CalibrationRecord:
    """Radyometrik kalibrasyon kaydi.

    * KR-018 / KR-082 -- Tam radyometrik kalibrasyon zorunlulugu.
    * Calibration Gate: calibrated yoksa job acma.
    * QC Gate: PASS/WARN/FAIL kararini sakla, UI'a tasi, audit trail uret.
    """

    calibration_record_id: uuid.UUID
    mission_id: uuid.UUID
    status: CalibrationStatus
    created_at: datetime
    batch_id: Optional[uuid.UUID] = None
    calibration_manifest: Optional[Dict[str, Any]] = None  # JSONB
    processing_report_uri: Optional[str] = None
    calibration_result_uri: Optional[str] = None
    qc_report_uri: Optional[str] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _touch(self) -> None:
        """CalibrationRecord has no updated_at; use status transitions."""
        pass

    # ------------------------------------------------------------------
    # Domain methods
    # ------------------------------------------------------------------
    def mark_calibrated(self, calibration_result_uri: str) -> None:
        """Kalibrasyon basariyla tamamlandi (PENDING -> CALIBRATED).

        calibration_result_uri zorunludur (KR-018: kalibrasyon ciktisi).
        """
        if self.status != CalibrationStatus.PENDING:
            raise ValueError(
                f"Can only mark_calibrated from PENDING, current: {self.status.value}"
            )
        if not calibration_result_uri or not calibration_result_uri.strip():
            raise ValueError(
                "calibration_result_uri is required to mark as calibrated (KR-018)"
            )
        self.status = CalibrationStatus.CALIBRATED
        self.calibration_result_uri = calibration_result_uri

    def mark_failed(self) -> None:
        """Kalibrasyon basarisiz (PENDING -> FAILED)."""
        if self.status != CalibrationStatus.PENDING:
            raise ValueError(
                f"Can only mark_failed from PENDING, current: {self.status.value}"
            )
        self.status = CalibrationStatus.FAILED
