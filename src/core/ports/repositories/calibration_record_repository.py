# PATH: src/core/ports/repositories/calibration_record_repository.py
# DESC: CalibrationRecord erişimi için repository portu.
# SSOT: KR-018/KR-082 (tam radyometrik kalibrasyon zorunluluğu)
"""
CalibrationRecordRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  CalibrationRecord entity'sinin kalıcı depolama erişimini soyutlar.
  Radyometrik kalibrasyon kayıtlarının saklanması ve sorgulanmasını kapsar.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (calibration_record_id, mission_id vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[CalibrationRecord]).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.

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

from src.core.domain.entities.calibration_record import (
    CalibrationRecord,
    CalibrationStatus,
)


class CalibrationRecordRepository(ABC):
    """CalibrationRecord persistence port (KR-018, KR-082).

    Radyometrik kalibrasyon kayıtlarının saklanması ve sorgulanmasını soyutlar.
    Infrastructure katmanı bu interface'i implemente eder.

    KR-018 hard gate: AnalysisJob başlatmadan önce CALIBRATED kaydı doğrulanır.
    Idempotency: calibration_record_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, record: CalibrationRecord) -> None:
        """CalibrationRecord kaydet (insert veya update).

        Args:
            record: Kaydedilecek CalibrationRecord entity'si.

        Raises:
            IntegrityError: calibration_record_id benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, calibration_record_id: uuid.UUID) -> Optional[CalibrationRecord]:
        """calibration_record_id ile CalibrationRecord getir.

        Args:
            calibration_record_id: Aranacak kayıt ID'si.

        Returns:
            CalibrationRecord veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_mission_id(self, mission_id: uuid.UUID) -> List[CalibrationRecord]:
        """Bir mission'a ait tüm kalibrasyon kayıtlarını getir.

        Args:
            mission_id: İlişkili Mission ID'si.

        Returns:
            CalibrationRecord listesi (boş olabilir).
        """

    @abstractmethod
    async def find_by_mission_id_and_status(
        self,
        mission_id: uuid.UUID,
        status: CalibrationStatus,
    ) -> Optional[CalibrationRecord]:
        """Bir mission için belirli durumdaki kalibrasyon kaydını getir.

        KR-018 hard gate kontrolü için kullanılır:
        CALIBRATED kaydı yoksa AnalysisJob başlatılamaz.

        Args:
            mission_id: İlişkili Mission ID'si.
            status: Aranacak kalibrasyon durumu.

        Returns:
            CalibrationRecord veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, calibration_record_id: uuid.UUID) -> None:
        """CalibrationRecord sil.

        Args:
            calibration_record_id: Silinecek kayıt ID'si.

        Raises:
            KeyError: calibration_record_id bulunamadığında.
        """
