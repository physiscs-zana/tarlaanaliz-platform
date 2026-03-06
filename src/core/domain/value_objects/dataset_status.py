# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/value_objects/dataset_status.py
# DESC: DatasetStatus VO; KR-072 9+1 durum state machine.
# SSOT: TARLAANALIZ_SSOT_v1_2_0.txt — KR-072 (Dataset durum makinesi)
"""
DatasetStatus value object.

KR-072: Dataset tam durum makinesi.

Normal akış (9 durum):
  RAW_INGESTED
  → RAW_SCANNED_EDGE_OK       (AV1 edge taraması tamamlandı)
  → RAW_HASH_SEALED           (SHA-256 manifest mühürlendi)
  → CALIBRATED                (Pix4Dfields radyometrik kalibrasyon)
  → CALIBRATED_SCANNED_CENTER_OK  (AV2 merkez taraması tamamlandı)
  → DISPATCHED_TO_WORKER      (Worker kuyruğuna gönderildi)
  → ANALYZED                  (Worker analizi tamamladı)
  → DERIVED_PUBLISHED         (Türev sonuçlar yayınlandı)
  → ARCHIVED                  (Arşivlendi)

Hata durumu (1 durum):
  REJECTED_QUARANTINE         (AV taraması veya hash hatası — karantina)

Geçiş kuralları:
- Her geçiş için manifest + SHA-256 zorunlu.
- AV1 raporu olmadan RAW_SCANNED_EDGE_OK'a geçilemez.
- AV2 raporu olmadan CALIBRATED_SCANNED_CENTER_OK'a geçilemez.
- Herhangi bir aşamada hash uyumsuzluğu veya virüs tespiti → REJECTED_QUARANTINE.
- Worker inbound HTTP almaz; sadece queue'dan consume eder (KR-070).
"""

from __future__ import annotations

from enum import Enum


class DatasetStatus(str, Enum):
    """Dataset durum makinesi (KR-072).

    9 normal durum + 1 hata durumu.
    """

    # Normal akış
    RAW_INGESTED = "RAW_INGESTED"
    RAW_SCANNED_EDGE_OK = "RAW_SCANNED_EDGE_OK"
    RAW_HASH_SEALED = "RAW_HASH_SEALED"
    CALIBRATED = "CALIBRATED"
    CALIBRATED_SCANNED_CENTER_OK = "CALIBRATED_SCANNED_CENTER_OK"
    DISPATCHED_TO_WORKER = "DISPATCHED_TO_WORKER"
    ANALYZED = "ANALYZED"
    DERIVED_PUBLISHED = "DERIVED_PUBLISHED"
    ARCHIVED = "ARCHIVED"

    # Hata durumu
    REJECTED_QUARANTINE = "REJECTED_QUARANTINE"


# Geçerli durum geçişleri (KR-072)
VALID_DATASET_TRANSITIONS: dict[DatasetStatus, frozenset[DatasetStatus]] = {
    DatasetStatus.RAW_INGESTED: frozenset(
        {
            DatasetStatus.RAW_SCANNED_EDGE_OK,
            DatasetStatus.REJECTED_QUARANTINE,
        }
    ),
    DatasetStatus.RAW_SCANNED_EDGE_OK: frozenset(
        {
            DatasetStatus.RAW_HASH_SEALED,
            DatasetStatus.REJECTED_QUARANTINE,
        }
    ),
    DatasetStatus.RAW_HASH_SEALED: frozenset(
        {
            DatasetStatus.CALIBRATED,
            DatasetStatus.REJECTED_QUARANTINE,
        }
    ),
    DatasetStatus.CALIBRATED: frozenset(
        {
            DatasetStatus.CALIBRATED_SCANNED_CENTER_OK,
            DatasetStatus.REJECTED_QUARANTINE,
        }
    ),
    DatasetStatus.CALIBRATED_SCANNED_CENTER_OK: frozenset(
        {
            DatasetStatus.DISPATCHED_TO_WORKER,
            DatasetStatus.REJECTED_QUARANTINE,
        }
    ),
    DatasetStatus.DISPATCHED_TO_WORKER: frozenset(
        {
            DatasetStatus.ANALYZED,
            DatasetStatus.REJECTED_QUARANTINE,
        }
    ),
    DatasetStatus.ANALYZED: frozenset(
        {
            DatasetStatus.DERIVED_PUBLISHED,
            DatasetStatus.REJECTED_QUARANTINE,
        }
    ),
    DatasetStatus.DERIVED_PUBLISHED: frozenset(
        {
            DatasetStatus.ARCHIVED,
        }
    ),
    DatasetStatus.ARCHIVED: frozenset(),  # terminal
    DatasetStatus.REJECTED_QUARANTINE: frozenset(),  # terminal
}

# Terminal durumlar
TERMINAL_DATASET_STATUSES: frozenset[DatasetStatus] = frozenset(
    {
        DatasetStatus.ARCHIVED,
        DatasetStatus.REJECTED_QUARANTINE,
    }
)

# AV taraması gerektiren geçişler
AV1_REQUIRED_FOR: frozenset[DatasetStatus] = frozenset(
    {
        DatasetStatus.RAW_SCANNED_EDGE_OK,
    }
)

AV2_REQUIRED_FOR: frozenset[DatasetStatus] = frozenset(
    {
        DatasetStatus.CALIBRATED_SCANNED_CENTER_OK,
    }
)


def is_valid_dataset_transition(
    current: DatasetStatus,
    target: DatasetStatus,
) -> bool:
    """Verilen geçiş KR-072 kurallarına uygun mu?"""
    allowed = VALID_DATASET_TRANSITIONS.get(current, frozenset())
    return target in allowed


def requires_av1_report(target: DatasetStatus) -> bool:
    """Bu duruma geçiş için AV1 (edge) raporu zorunlu mu?"""
    return target in AV1_REQUIRED_FOR


def requires_av2_report(target: DatasetStatus) -> bool:
    """Bu duruma geçiş için AV2 (merkez) raporu zorunlu mu?"""
    return target in AV2_REQUIRED_FOR


def is_quarantined(status: DatasetStatus) -> bool:
    """Dataset karantinada mı?"""
    return status == DatasetStatus.REJECTED_QUARANTINE
