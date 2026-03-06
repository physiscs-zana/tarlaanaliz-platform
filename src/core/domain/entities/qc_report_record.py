# PATH: src/core/domain/entities/qc_report_record.py
# DESC: QCReportRecord; kalibrasyon sonrasi kalite kontrol raporu (KR-018).
# SSOT: KR-018/KR-082 (QC Gate)
"""
QCReportRecord domain entity.

Kalibrasyon sonrasi kalite kontrol raporu.
QC Gate: PASS/WARN/FAIL kararini sakla, UI'a tasi, audit trail uret (KR-018).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class QCStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class QCRecommendedAction(str, Enum):
    PROCEED = "PROCEED"
    REVIEW = "REVIEW"
    RETRY = "RETRY"


@dataclass
class QCReportRecord:
    """Kalite kontrol raporu domain entity'si.

    * KR-018 -- QC Gate: PASS/WARN/FAIL + flags + recommended_action.
    * Flags: blur, overexposure, missing_bands vb. (JSONB).
    """

    qc_report_id: uuid.UUID
    calibration_record_id: uuid.UUID
    status: QCStatus
    recommended_action: QCRecommendedAction
    created_at: datetime
    flags: Optional[Dict[str, Any]] = None  # JSONB: blur, overexposure, missing_bands
    notes: Optional[str] = None

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------
    @property
    def is_passable(self) -> bool:
        """PASS veya WARN ise islem devam edebilir."""
        return self.status in (QCStatus.PASS, QCStatus.WARN)
