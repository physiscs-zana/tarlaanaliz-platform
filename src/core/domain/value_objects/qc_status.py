# PATH: src/core/domain/value_objects/qc_status.py
# DESC: QCStatus VO; QC durum enum (KR-082).
# SSOT: KR-018 (kalibrasyon hard gate), KR-082 (QC gate)
"""
QCStatus value object.

Kalite kontrol durumunu ve onerilen aksiyonu temsil eden enum'lar.
KR-018 hard gate: calibrated/QC kaniti olmadan AnalysisJob baslatilamaz.
Entity'deki QCStatus enum'u ile SSOT uyumludur.
"""

from __future__ import annotations

from enum import Enum


class QCStatus(str, Enum):
    """KR-082 kanonik QC durumlari.

    * PASS -- Kalite kontrol basarili; islem devam edebilir.
    * WARN -- Uyari; islem devam edebilir ama dikkat gerekir.
    * FAIL -- Kalite kontrol basarisiz; analiz baslatilamaz (KR-018 hard gate).
    """

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class QCRecommendedAction(str, Enum):
    """QC raporu sonrasi onerilen aksiyon.

    * PROCEED -- Islem devam edebilir (PASS durumunda).
    * REVIEW  -- Manuel inceleme gerekli (WARN durumunda).
    * RETRY   -- Yeniden deneme gerekli (FAIL durumunda).
    """

    PROCEED = "PROCEED"
    REVIEW = "REVIEW"
    RETRY = "RETRY"


def is_qc_passable(status: QCStatus) -> bool:
    """PASS veya WARN ise islem devam edebilir."""
    return status in (QCStatus.PASS, QCStatus.WARN)


def is_qc_blocking(status: QCStatus) -> bool:
    """FAIL ise analiz baslatilamaz (KR-018 hard gate)."""
    return status == QCStatus.FAIL
