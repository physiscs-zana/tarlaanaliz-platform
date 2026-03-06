# PATH: src/core/ports/repositories/expert_review_repository.py
# DESC: ExpertReviewRepository portu (KR-019).
# SSOT: KR-019 (expert portal / uzman inceleme), KR-029 (training feedback)
"""
ExpertReviewRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  ExpertReview entity'sinin kalıcı depolama erişimini soyutlar.
  Uzman incelemelerinin atanması, takibi ve sorgulanmasını kapsar.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (review_id, expert_id, mission_id vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[ExpertReview]).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  Ownership check zorunlu: uzman yalnızca kendisine atanmış incelemeleri görür (KR-019).

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

from src.core.domain.entities.expert_review import ExpertReview, ExpertReviewStatus


class ExpertReviewRepository(ABC):
    """ExpertReview persistence port (KR-019, KR-029).

    Uzman incelemelerinin saklanması ve sorgulanmasını soyutlar.
    Infrastructure katmanı bu interface'i implemente eder.

    Ownership check: uzman yalnızca kendi incelemelerini görebilir.
    Idempotency: review_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, review: ExpertReview) -> None:
        """ExpertReview kaydet (insert veya update).

        Args:
            review: Kaydedilecek ExpertReview entity'si.

        Raises:
            IntegrityError: review_id benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, review_id: uuid.UUID) -> Optional[ExpertReview]:
        """review_id ile ExpertReview getir.

        Args:
            review_id: Aranacak inceleme ID'si.

        Returns:
            ExpertReview veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_expert_id(
        self,
        expert_id: uuid.UUID,
        *,
        status: Optional[ExpertReviewStatus] = None,
    ) -> List[ExpertReview]:
        """Bir uzmana ait incelemeleri getir (durum filtresi opsiyonel).

        Ownership check: uzmana yalnızca kendi incelemeleri döner (KR-019).

        Args:
            expert_id: İlişkili Expert ID'si.
            status: Opsiyonel durum filtresi.

        Returns:
            ExpertReview listesi (boş olabilir), assigned_at'e göre sıralı.
        """

    @abstractmethod
    async def list_by_mission_id(self, mission_id: uuid.UUID) -> List[ExpertReview]:
        """Bir mission'a ait tüm uzman incelemelerini getir.

        Args:
            mission_id: İlişkili Mission ID'si.

        Returns:
            ExpertReview listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_analysis_result_id(self, analysis_result_id: uuid.UUID) -> List[ExpertReview]:
        """Bir analiz sonucuna ait tüm uzman incelemelerini getir.

        Args:
            analysis_result_id: İlişkili AnalysisResult ID'si.

        Returns:
            ExpertReview listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_status(self, status: ExpertReviewStatus) -> List[ExpertReview]:
        """Belirli durumdaki tüm incelemeleri getir.

        Kuyruk yönetimi ve iş dağıtımı için kullanılır.

        Args:
            status: İnceleme durumu (PENDING, IN_PROGRESS, COMPLETED, REJECTED).

        Returns:
            ExpertReview listesi (boş olabilir).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, review_id: uuid.UUID) -> None:
        """ExpertReview sil.

        Args:
            review_id: Silinecek inceleme ID'si.

        Raises:
            KeyError: review_id bulunamadığında.
        """
