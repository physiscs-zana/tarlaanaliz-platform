# PATH: src/core/domain/entities/analysis_job.py
# DESC: AnalysisJob; kalibrasyon gate (KR-018), QC gate, worker dispatch.
# SSOT: KR-017 (YZ analiz izolasyonu), KR-018/KR-082 (kalibrasyon hard gate)
"""
AnalysisJob domain entity.

Worker, KR-018 kalibrasyon "hard gate" sarti saglanmadan isi kabul etmez.
requires_calibrated=true ile acilir (KR-017).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class AnalysisJobStatus(str, Enum):
    """KR-017/KR-018 kanonik analiz is durumlari."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class AnalysisJob:
    """YZ analiz isi domain entity'si.

    * KR-017 -- YZ modeli ile analiz (izolasyon + tek yonlu akis + job semantigi).
    * KR-018 / KR-082 -- Tam radyometrik kalibrasyon zorunlulugu (hard gate).
    * KR-018 v1.2.0 -- available_bands zorunlu; band_class Graceful Degradation.
    * KR-081 -- Contract-first: AnalysisJob JSON Schema.
    """

    analysis_job_id: uuid.UUID
    mission_id: uuid.UUID
    field_id: uuid.UUID
    crop_type: str
    analysis_type: str
    model_id: str
    model_version: str
    status: AnalysisJobStatus
    created_at: datetime
    updated_at: datetime
    requires_calibrated: bool = True
    calibration_record_id: Optional[uuid.UUID] = None
    # KR-018/KR-082 v1.2.0: Graceful Degradation
    available_bands: tuple[str, ...] = ()  # intake_manifest.available_bands[]
    band_class: str = ""  # BASIC_4BAND | EXTENDED_5BAND

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if not self.crop_type:
            raise ValueError("crop_type is required")
        if not self.analysis_type:
            raise ValueError("analysis_type is required")
        if not self.model_id:
            raise ValueError("model_id is required (KR-017)")
        if not self.model_version:
            raise ValueError("model_version is required (KR-017)")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Domain methods
    # ------------------------------------------------------------------
    def attach_calibration(self, calibration_record_id: uuid.UUID) -> None:
        """Kalibrasyon kaydini isle bagla."""
        self.calibration_record_id = calibration_record_id
        self._touch()

    def start_processing(self) -> None:
        """Analizi baslat (KR-018 hard gate).

        requires_calibrated=true ise calibration_record_id zorunludur.
        Worker ham DN veya kalibrasyonu belirsiz veriyi kabul ETMEZ.
        """
        if self.status != AnalysisJobStatus.PENDING:
            raise ValueError(
                f"Can only start_processing from PENDING, current: {self.status.value}"
            )
        # KR-018 hard gate
        if self.requires_calibrated and self.calibration_record_id is None:
            raise ValueError(
                "Cannot start processing: requires_calibrated=True but "
                "calibration_record_id is not set (KR-018 hard gate). "
                "Calibrated dataset uretilmeden AnalysisJob baslatilamaz."
            )
        # KR-018 v1.2.0: available_bands zorunlu
        if not self.available_bands:
            raise ValueError(
                "Cannot start processing: available_bands is empty "
                "(KR-018 v1.2.0: intake_manifest.available_bands[] zorunlu)."
            )
        self.status = AnalysisJobStatus.PROCESSING
        self._touch()

    def complete(self) -> None:
        """Analiz basariyla tamamlandi (PROCESSING -> COMPLETED)."""
        if self.status != AnalysisJobStatus.PROCESSING:
            raise ValueError(
                f"Can only complete from PROCESSING, current: {self.status.value}"
            )
        self.status = AnalysisJobStatus.COMPLETED
        self._touch()

    def fail(self) -> None:
        """Analiz basarisiz oldu (PENDING|PROCESSING -> FAILED)."""
        if self.status not in (AnalysisJobStatus.PENDING, AnalysisJobStatus.PROCESSING):
            raise ValueError(
                f"Can only fail from PENDING or PROCESSING, current: {self.status.value}"
            )
        self.status = AnalysisJobStatus.FAILED
        self._touch()
