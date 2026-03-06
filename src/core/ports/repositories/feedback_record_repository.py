# PATH: src/core/ports/repositories/feedback_record_repository.py
# DESC: FeedbackRecordRepository portu (KR-019).
# SSOT: KR-029 (YZ eğitim geri bildirimi), KR-019 (expert portal)
"""
FeedbackRecordRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  FeedbackRecord entity'sinin kalıcı depolama erişimini soyutlar.
  Uzman geri bildirimlerinin YZ modeline aktarılmasını kapsar.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (feedback_id, review_id, mission_id vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[FeedbackRecord]).

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
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from src.core.domain.entities.feedback_record import FeedbackRecord


class FeedbackRecordRepository(ABC):
    """FeedbackRecord persistence port (KR-029, KR-019).

    Uzman geri bildirimlerinin saklanması ve sorgulanmasını soyutlar.
    YZ eğitim pipeline'ına veri sağlar.
    Infrastructure katmanı bu interface'i implemente eder.

    Idempotency: feedback_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, record: FeedbackRecord) -> None:
        """FeedbackRecord kaydet (insert veya update).

        Args:
            record: Kaydedilecek FeedbackRecord entity'si.

        Raises:
            IntegrityError: feedback_id benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, feedback_id: uuid.UUID) -> Optional[FeedbackRecord]:
        """feedback_id ile FeedbackRecord getir.

        Args:
            feedback_id: Aranacak geri bildirim ID'si.

        Returns:
            FeedbackRecord veya bulunamazsa None.
        """

    @abstractmethod
    async def find_by_review_id(self, review_id: uuid.UUID) -> Optional[FeedbackRecord]:
        """review_id ile FeedbackRecord getir.

        Bir ExpertReview'ın ürettiği geri bildirimi bulmak için kullanılır.

        Args:
            review_id: İlişkili ExpertReview ID'si.

        Returns:
            FeedbackRecord veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_mission_id(self, mission_id: uuid.UUID) -> List[FeedbackRecord]:
        """Bir mission'a ait tüm geri bildirimleri getir.

        Args:
            mission_id: İlişkili Mission ID'si.

        Returns:
            FeedbackRecord listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_model_id(self, model_id: str) -> List[FeedbackRecord]:
        """Belirli bir YZ modeline ait tüm geri bildirimleri getir.

        YZ eğitim pipeline'ı için model bazlı feedback export'u.

        Args:
            model_id: YZ model tanımlayıcısı.

        Returns:
            FeedbackRecord listesi (boş olabilir), created_at'e göre sıralı.
        """

    @abstractmethod
    async def list_by_verdict(self, verdict: str) -> List[FeedbackRecord]:
        """Belirli verdict'e göre geri bildirimleri getir.

        Args:
            verdict: Karar türü (confirmed|corrected|rejected|needs_more_expert).

        Returns:
            FeedbackRecord listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_training_grade(self, training_grade: str) -> List[FeedbackRecord]:
        """Belirli eğitim notuna göre geri bildirimleri getir.

        Args:
            training_grade: Eğitim notu (A|B|C|D|REJECT).

        Returns:
            FeedbackRecord listesi (boş olabilir).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, feedback_id: uuid.UUID) -> None:
        """FeedbackRecord sil.

        Args:
            feedback_id: Silinecek geri bildirim ID'si.

        Raises:
            KeyError: feedback_id bulunamadığında.
        """
