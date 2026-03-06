# PATH: src/core/domain/value_objects/qc_report.py
# DESC: QCReport VO; kalite kontrol raporu ve threshold kurallari.
# SSOT: KR-018 (kalibrasyon hard gate), KR-082 (QC gate)
"""
QCReport value object.

Kalite kontrol raporu sonucunu temsil eder; QCFlag listesi, genel durum
ve onerilen aksiyon icerir. KR-018 hard gate karari bu VO uzerinden verilir.
Entity katmanindaki QCReportRecord tam kaydi temsil eder; bu VO
domain genelinde tasinabilir hafif referanstir.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.core.domain.value_objects.qc_flag import QCFlag, QCFlagSeverity
from src.core.domain.value_objects.qc_status import QCStatus, QCRecommendedAction


@dataclass(frozen=True)
class QCReport:
    """Immutable QC raporu.

    * KR-018 -- Hard gate: FAIL durumunda AnalysisJob baslatilamaz.
    * KR-082 -- QC gate mekanizmasi.

    frozen=True: olusturulduktan sonra alanlari degistirilemez.
    """

    report_id: uuid.UUID
    calibration_record_id: uuid.UUID
    status: QCStatus
    recommended_action: QCRecommendedAction
    created_at: datetime
    flags: tuple[QCFlag, ...] = ()
    notes: Optional[str] = None

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if not isinstance(self.status, QCStatus):
            raise TypeError(f"status must be QCStatus, got {type(self.status).__name__}")
        if not isinstance(self.recommended_action, QCRecommendedAction):
            raise TypeError(
                f"recommended_action must be QCRecommendedAction, got {type(self.recommended_action).__name__}"
            )
        # FAIL durumunda PROCEED onerisi mantiksal celiskidir
        if self.status == QCStatus.FAIL and self.recommended_action == QCRecommendedAction.PROCEED:
            raise ValueError("QCStatus.FAIL cannot have recommended_action=PROCEED (KR-018)")

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------
    @property
    def is_passable(self) -> bool:
        """PASS veya WARN ise islem devam edebilir (KR-018)."""
        return self.status in (QCStatus.PASS, QCStatus.WARN)

    @property
    def is_blocking(self) -> bool:
        """FAIL ise analiz baslatilamaz (KR-018 hard gate)."""
        return self.status == QCStatus.FAIL

    @property
    def critical_flags(self) -> tuple[QCFlag, ...]:
        """Yalnizca CRITICAL severity bayraklar."""
        return tuple(f for f in self.flags if f.severity == QCFlagSeverity.CRITICAL)

    @property
    def has_critical_flags(self) -> bool:
        return len(self.critical_flags) > 0

    @property
    def flag_count(self) -> int:
        return len(self.flags)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, object]:
        return {
            "report_id": str(self.report_id),
            "calibration_record_id": str(self.calibration_record_id),
            "status": self.status.value,
            "recommended_action": self.recommended_action.value,
            "created_at": self.created_at.isoformat(),
            "flags": [f.to_dict() for f in self.flags],
            "notes": self.notes,
        }
