# PATH: src/core/ports/repositories/analysis_result_repository.py
# DESC: AnalysisResult sorgulaması için repository portu.
# SSOT: KR-081 (contract-first JSON Schema), KR-025 (analiz içeriği)
"""
AnalysisResultRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  AnalysisResult entity'sinin kalıcı depolama erişimini soyutlar.
  YZ analiz sonuçlarının saklanması ve sorgulanmasını kapsar.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (result_id, mission_id, field_id vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[AnalysisResult]).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: analiz sonuçları PII içermez; field_id ile ilişkilendirilir.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel).

Observability (log fields/metrics/traces):
  latency, error_code, retries; DB query time.

Testler: Contract test (port), integration test (DB/external stub), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon (_impl) taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from src.core.domain.entities.analysis_result import AnalysisResult


class AnalysisResultRepository(ABC):
    """AnalysisResult persistence port (KR-081, KR-025).

    YZ analiz sonuçlarının saklanması ve sorgulanmasını soyutlar.
    Infrastructure katmanı bu interface'i implemente eder (SQLAlchemy vb.).

    Idempotency: result_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, result: AnalysisResult) -> None:
        """AnalysisResult kaydet (insert veya update).

        Args:
            result: Kaydedilecek AnalysisResult entity'si.

        Raises:
            IntegrityError: result_id veya benzersizlik kısıtı ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, result_id: uuid.UUID) -> Optional[AnalysisResult]:
        """result_id ile AnalysisResult getir.

        Args:
            result_id: Aranacak sonuç ID'si.

        Returns:
            AnalysisResult veya bulunamazsa None.
        """

    @abstractmethod
    async def find_by_analysis_job_id(self, analysis_job_id: uuid.UUID) -> Optional[AnalysisResult]:
        """analysis_job_id ile AnalysisResult getir.

        Bir AnalysisJob'ın ürettiği sonuç.

        Args:
            analysis_job_id: İlişkili AnalysisJob ID'si.

        Returns:
            AnalysisResult veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_mission_id(self, mission_id: uuid.UUID) -> List[AnalysisResult]:
        """Bir mission'a ait tüm analiz sonuçlarını getir.

        Args:
            mission_id: İlişkili Mission ID'si.

        Returns:
            AnalysisResult listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_field_id(self, field_id: uuid.UUID) -> List[AnalysisResult]:
        """Bir tarlaya ait tüm analiz sonuçlarını getir.

        Tarla bazlı geçmiş analiz raporlarını listelemek için kullanılır.

        Args:
            field_id: İlişkili Field ID'si.

        Returns:
            AnalysisResult listesi (boş olabilir), created_at'e göre sıralı.
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, result_id: uuid.UUID) -> None:
        """AnalysisResult sil.

        Args:
            result_id: Silinecek sonuç ID'si.

        Raises:
            KeyError: result_id bulunamadığında.
        """
