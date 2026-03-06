# PATH: src/core/ports/repositories/expert_repository.py
# DESC: ExpertRepository portu (KR-019).
# SSOT: KR-019 (expert portal / uzman inceleme)
"""
ExpertRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  Expert entity'sinin kalıcı depolama erişimini soyutlar.
  Uzman hesaplarının yönetimini kapsar (curated onboarding, ADMIN kontrolü).

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (expert_id, user_id, province vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[Expert]).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII GÖRÜNMEZ (KR-019): uzman yalnızca kendisine atanmış incelemeleri görür.

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

from src.core.domain.entities.expert import Expert, ExpertStatus


class ExpertRepository(ABC):
    """Expert persistence port (KR-019).

    Uzman hesaplarının kalıcı depolama erişimini soyutlar.
    Infrastructure katmanı bu interface'i implemente eder.

    Uzman hesabı self-signup DEĞİLDİR: ADMIN kontrolü ile açılır.
    Idempotency: expert_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, expert: Expert) -> None:
        """Expert kaydet (insert veya update).

        Args:
            expert: Kaydedilecek Expert entity'si.

        Raises:
            IntegrityError: expert_id benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, expert_id: uuid.UUID) -> Optional[Expert]:
        """expert_id ile Expert getir.

        Args:
            expert_id: Aranacak uzman ID'si.

        Returns:
            Expert veya bulunamazsa None.
        """

    @abstractmethod
    async def find_by_user_id(self, user_id: uuid.UUID) -> Optional[Expert]:
        """user_id ile Expert getir.

        Bir kullanıcının uzman profilini bulmak için kullanılır.

        Args:
            user_id: İlişkili User ID'si.

        Returns:
            Expert veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_province(self, province: str) -> List[Expert]:
        """Belirli bir ildeki uzmanları getir.

        Args:
            province: İl adı.

        Returns:
            Expert listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_status(self, status: ExpertStatus) -> List[Expert]:
        """Belirli durumdaki uzmanları getir.

        Args:
            status: Uzman durumu (ACTIVE, INACTIVE, SUSPENDED).

        Returns:
            Expert listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_specialization(self, specialization: str) -> List[Expert]:
        """Belirli uzmanlık alanındaki uzmanları getir.

        Args:
            specialization: Uzmanlık alanı (ör. 'cotton_disease', 'pest').

        Returns:
            Expert listesi (boş olabilir).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, expert_id: uuid.UUID) -> None:
        """Expert sil.

        Args:
            expert_id: Silinecek uzman ID'si.

        Raises:
            KeyError: expert_id bulunamadığında.
        """
