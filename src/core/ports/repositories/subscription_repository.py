# PATH: src/core/ports/repositories/subscription_repository.py
# DESC: SubscriptionRepository portu (KR-015-5, KR-022).
# SSOT: KR-027 (abonelik planlayıcı), KR-015-5 (tarama takvimi), KR-033 (ödeme)
"""
SubscriptionRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  Subscription entity'sinin kalıcı depolama erişimini soyutlar.
  Yıllık abonelik oluşturma, güncelleme, scheduler sorguları ve yaşam döngüsü yönetimi.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (subscription_id, farmer_user_id, field_id vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[Subscription]).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  KR-033: PAID olmadan Subscription ACTIVE olamaz.

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

from src.core.domain.entities.subscription import Subscription, SubscriptionStatus


class SubscriptionRepository(ABC):
    """Subscription persistence port (KR-027, KR-015-5, KR-033).

    Aboneliklerin kalıcı depolama erişimini soyutlar.
    Infrastructure katmanı bu interface'i implemente eder.

    KR-033: PAID olmadan Subscription ACTIVE olamaz (ödeme doğrulama caller sorumluluğunda).
    KR-027: Scheduler due abonelikleri sorgular ve Mission üretir.
    Idempotency: subscription_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, subscription: Subscription) -> None:
        """Subscription kaydet (insert veya update).

        Args:
            subscription: Kaydedilecek Subscription entity'si.

        Raises:
            IntegrityError: subscription_id benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, subscription_id: uuid.UUID) -> Optional[Subscription]:
        """subscription_id ile Subscription getir.

        Args:
            subscription_id: Aranacak abonelik ID'si.

        Returns:
            Subscription veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_farmer_user_id(
        self,
        farmer_user_id: uuid.UUID,
        *,
        status: Optional[SubscriptionStatus] = None,
    ) -> List[Subscription]:
        """Bir çiftçinin aboneliklerini getir (durum filtresi opsiyonel).

        Args:
            farmer_user_id: Çiftçi User ID'si.
            status: Opsiyonel durum filtresi.

        Returns:
            Subscription listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_field_id(self, field_id: uuid.UUID) -> List[Subscription]:
        """Bir tarlaya ait tüm abonelikleri getir.

        Args:
            field_id: İlişkili Field ID'si.

        Returns:
            Subscription listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_status(self, status: SubscriptionStatus) -> List[Subscription]:
        """Belirli durumdaki tüm abonelikleri getir.

        Admin paneli, raporlama ve toplu işlemler için kullanılır.

        Args:
            status: Abonelik durumu (KR-027 kanonik durumlar).

        Returns:
            Subscription listesi (boş olabilir).
        """

    @abstractmethod
    async def list_due(self) -> List[Subscription]:
        """Zamanı gelmiş (due) abonelikleri getir (KR-027 scheduler).

        status=ACTIVE ve next_due_at <= now olan abonelikleri döner.
        Scheduler bu metodu periyodik olarak çağırarak Mission üretir.

        Returns:
            Due Subscription listesi (boş olabilir).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, subscription_id: uuid.UUID) -> None:
        """Subscription sil.

        Args:
            subscription_id: Silinecek abonelik ID'si.

        Raises:
            KeyError: subscription_id bulunamadığında.
        """
