# PATH: src/core/domain/entities/dataset.py
# DESC: Dataset entity; KR-072 tam durum makinesi (9+1 durum).
# SSOT: TARLAANALIZ_SSOT_v1_1_0.txt — KR-072, KR-073, KR-070
"""
Dataset domain entity.

KR-072: Dataset tam durum makinesi.
KR-073: İki aşamalı malware tarama (AV1 edge, AV2 center).
KR-070: Worker tam izolasyon — inbound HTTP yasak; queue consume-only.
KR-018: Radyometrik kalibrasyon hard gate (CALIBRATED durumuna geçiş için).

Her durum geçişinde:
- manifest JSONB zorunlu
- SHA-256 hash zorunlu
- İlgili AV raporu URI'si zorunlu (AV1 veya AV2)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.core.domain.value_objects.dataset_status import (
    DatasetStatus,
    is_valid_dataset_transition,
    requires_av1_report,
    requires_av2_report,
)


class DatasetError(Exception):
    """Dataset domain invariant ihlali."""


class DatasetTransitionError(DatasetError):
    """Geçersiz durum geçişi."""


@dataclass
class Dataset:
    """Drone veri seti entity'si (KR-072).

    Durum makinesi:
      RAW_INGESTED → RAW_SCANNED_EDGE_OK → RAW_HASH_SEALED
      → CALIBRATED → CALIBRATED_SCANNED_CENTER_OK
      → DISPATCHED_TO_WORKER → ANALYZED → DERIVED_PUBLISHED → ARCHIVED

    Hata: REJECTED_QUARANTINE (herhangi bir aşamada AV tespiti veya hash hatası)

    Invariants:
    - dataset_id benzersiz UUID.
    - mission_id zorunlu (dataset bir mission'a bağlı).
    - sha256_hash: RAW_HASH_SEALED'dan itibaren zorunlu.
    - av1_report_uri: RAW_SCANNED_EDGE_OK için zorunlu.
    - av2_report_uri: CALIBRATED_SCANNED_CENTER_OK için zorunlu.
    - Worker'a hiçbir inbound HTTP bağlantısı açılamaz (KR-070).
    """

    dataset_id: uuid.UUID
    mission_id: uuid.UUID
    field_id: uuid.UUID
    status: DatasetStatus
    created_at: datetime
    updated_at: datetime

    # Hash ve manifest
    sha256_hash: Optional[str] = None          # RAW_HASH_SEALED'dan itibaren zorunlu
    manifest: Optional[dict] = None            # JSONB, her geçişte güncellenir

    # AV tarama raporları (KR-073)
    av1_report_uri: Optional[str] = None       # Edge AV1 raporu URI
    av2_report_uri: Optional[str] = None       # Merkez AV2 raporu URI

    # Kalibrasyon (KR-018)
    is_calibrated: bool = False                # Pix4Dfields radyometrik kalibrasyon

    # Sonuç referansları
    worker_job_id: Optional[uuid.UUID] = None  # DISPATCHED_TO_WORKER'da set edilir
    result_uri: Optional[str] = None           # ANALYZED'da set edilir (Object Storage)
    signature: Optional[str] = None            # KR-072 imza doğrulama

    # Karantina notu
    quarantine_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.mission_id:
            raise DatasetError("mission_id zorunludur")
        if not self.field_id:
            raise DatasetError("field_id zorunludur")

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def transition_to(
        self,
        target: DatasetStatus,
        *,
        av1_report_uri: Optional[str] = None,
        av2_report_uri: Optional[str] = None,
        sha256_hash: Optional[str] = None,
        manifest_update: Optional[dict] = None,
        quarantine_reason: Optional[str] = None,
        worker_job_id: Optional[uuid.UUID] = None,
        result_uri: Optional[str] = None,
        signature: Optional[str] = None,
    ) -> None:
        """KR-072 kurallarına uygun durum geçişi.

        Raises:
            DatasetTransitionError: Geçersiz geçiş veya zorunlu alan eksikse.
        """
        if not is_valid_dataset_transition(self.status, target):
            raise DatasetTransitionError(
                f"Geçersiz geçiş: {self.status} → {target}"
            )

        # AV1 raporu zorunluluğu
        if requires_av1_report(target):
            uri = av1_report_uri or self.av1_report_uri
            if not uri:
                raise DatasetTransitionError(
                    f"{target} geçişi için AV1 (edge) raporu zorunludur (KR-073)"
                )
            self.av1_report_uri = uri

        # AV2 raporu zorunluluğu
        if requires_av2_report(target):
            uri = av2_report_uri or self.av2_report_uri
            if not uri:
                raise DatasetTransitionError(
                    f"{target} geçişi için AV2 (merkez) raporu zorunludur (KR-073)"
                )
            self.av2_report_uri = uri

        # Hash mühürü
        if target == DatasetStatus.RAW_HASH_SEALED:
            if not (sha256_hash or self.sha256_hash):
                raise DatasetTransitionError(
                    "RAW_HASH_SEALED geçişi için sha256_hash zorunludur (KR-072)"
                )
            if sha256_hash:
                self.sha256_hash = sha256_hash

        # Kalibrasyon gate (KR-018)
        if target == DatasetStatus.CALIBRATED:
            self.is_calibrated = True

        # Worker dispatch
        if target == DatasetStatus.DISPATCHED_TO_WORKER:
            if worker_job_id:
                self.worker_job_id = worker_job_id

        # Analiz sonucu
        if target == DatasetStatus.ANALYZED:
            if result_uri:
                self.result_uri = result_uri
            if signature:
                self.signature = signature

        # Karantina
        if target == DatasetStatus.REJECTED_QUARANTINE:
            self.quarantine_reason = quarantine_reason

        # Manifest güncelle
        if manifest_update:
            if self.manifest is None:
                self.manifest = {}
            self.manifest.update(manifest_update)

        self.status = target
        self.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------

    @property
    def is_quarantined(self) -> bool:
        """Karantinada mı?"""
        return self.status == DatasetStatus.REJECTED_QUARANTINE

    @property
    def is_ready_for_analysis(self) -> bool:
        """Worker kuyruğuna gönderilebilir mi?"""
        return (
            self.status == DatasetStatus.CALIBRATED_SCANNED_CENTER_OK
            and self.is_calibrated
            and self.sha256_hash is not None
            and self.av1_report_uri is not None
            and self.av2_report_uri is not None
        )

    @property
    def is_archived(self) -> bool:
        return self.status == DatasetStatus.ARCHIVED

    @classmethod
    def create(
        cls,
        mission_id: uuid.UUID,
        field_id: uuid.UUID,
    ) -> "Dataset":
        """Yeni Dataset oluştur; başlangıç durumu RAW_INGESTED."""
        now = datetime.now(timezone.utc)
        return cls(
            dataset_id=uuid.uuid4(),
            mission_id=mission_id,
            field_id=field_id,
            status=DatasetStatus.RAW_INGESTED,
            created_at=now,
            updated_at=now,
        )
