# PATH: src/core/ports/repositories/qc_report_repository.py
# DESC: QCReportRepository portu.
# SSOT: KR-018 (QC Gate), KR-082 (QC akışı)
"""
QCReportRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  QCReportRecord entity'sinin kalıcı depolama erişimini soyutlar.
  Kalibrasyon sonrası kalite kontrol raporlarının oluşturulması ve sorgulanmasını kapsar.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (qc_report_id, calibration_record_id vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[QCReportRecord]).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  KR-018: calibrated/QC kanıtı olmadan AnalysisJob başlatılmamalıdır.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel).

Observability (log fields/metrics/traces):
  latency, error_code, retries; DB query time.

Testler: Contract test (port), integration test (DB/external stub), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon (_impl) taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
  KR-018 hard gate: calibrated/QC kanıtı olmadan AnalysisJob başlatılmamalıdır.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from src.core.domain.entities.qc_report_record import (
    QCReportRecord,
    QCStatus,
)


class QCReportRepository(ABC):
    """QCReportRecord persistence port (KR-018, KR-082).

    Kalite kontrol raporlarının kalıcı depolama erişimini soyutlar.
    Infrastructure katmanı bu interface'i implemente eder.

    KR-018 hard gate: QC PASS/WARN olmadan AnalysisJob başlatılamaz.
    Idempotency: qc_report_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, report: QCReportRecord) -> None:
        """QCReportRecord kaydet (insert veya update).

        Args:
            report: Kaydedilecek QCReportRecord entity'si.

        Raises:
            IntegrityError: qc_report_id benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, qc_report_id: uuid.UUID) -> Optional[QCReportRecord]:
        """qc_report_id ile QCReportRecord getir.

        Args:
            qc_report_id: Aranacak QC rapor ID'si.

        Returns:
            QCReportRecord veya bulunamazsa None.
        """

    @abstractmethod
    async def find_by_calibration_record_id(self, calibration_record_id: uuid.UUID) -> Optional[QCReportRecord]:
        """calibration_record_id ile QCReportRecord getir.

        KR-018 hard gate kontrolü için kalibrasyon kaydına ait QC raporunu bulur.

        Args:
            calibration_record_id: İlişkili CalibrationRecord ID'si.

        Returns:
            QCReportRecord veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_status(self, status: QCStatus) -> List[QCReportRecord]:
        """Belirli durumdaki tüm QC raporlarını getir.

        Raporlama, admin paneli ve QC istatistikleri için kullanılır.

        Args:
            status: QC durumu (PASS, WARN, FAIL).

        Returns:
            QCReportRecord listesi (boş olabilir).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, qc_report_id: uuid.UUID) -> None:
        """QCReportRecord sil.

        Args:
            qc_report_id: Silinecek QC rapor ID'si.

        Raises:
            KeyError: qc_report_id bulunamadığında.
        """
