# PATH: src/core/ports/repositories/payment_intent_repository.py
# DESC: PaymentIntentRepository portu.
# SSOT: KR-033 (ödeme ve manuel onay)
"""
PaymentIntentRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  PaymentIntent entity'sinin kalıcı depolama erişimini soyutlar.
  Ödeme niyetlerinin oluşturulması, güncellenmesi ve sorgulanmasını kapsar.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (payment_intent_id, payment_ref, target_id vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[PaymentIntent]).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: kart bilgileri asla core'da tutulmaz; tokenization provider'da.
  KR-033: PaymentIntent olmadan paid state olmaz; dekont + manuel onay + audit.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel). Çift tahsilat önleme kritik.

Observability (log fields/metrics/traces):
  latency, error_code, retries; DB query time.

Testler: Contract test (port), integration test (DB/external stub), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon (_impl) taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
  KR-033: PaymentIntent olmadan paid state olmaz; dekont + manuel onay + audit.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from src.core.domain.entities.payment_intent import (
    PaymentIntent,
    PaymentStatus,
    PaymentTargetType,
)


class PaymentIntentRepository(ABC):
    """PaymentIntent persistence port (KR-033).

    Ödeme niyetlerinin kalıcı depolama erişimini soyutlar.
    Infrastructure katmanı bu interface'i implemente eder.

    KR-033: PaymentIntent olmadan paid state olmaz.
    Idempotency: payment_intent_id ve payment_ref benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, intent: PaymentIntent) -> None:
        """PaymentIntent kaydet (insert veya update).

        Args:
            intent: Kaydedilecek PaymentIntent entity'si.

        Raises:
            IntegrityError: payment_intent_id veya payment_ref benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, payment_intent_id: uuid.UUID) -> Optional[PaymentIntent]:
        """payment_intent_id ile PaymentIntent getir.

        Args:
            payment_intent_id: Aranacak ödeme niyeti ID'si.

        Returns:
            PaymentIntent veya bulunamazsa None.
        """

    @abstractmethod
    async def find_by_payment_ref(self, payment_ref: str) -> Optional[PaymentIntent]:
        """payment_ref ile PaymentIntent getir.

        Benzersiz ödeme referansı (PAY-YYYYMMDD-XXXXXX) ile arama.

        Args:
            payment_ref: Benzersiz ödeme referansı.

        Returns:
            PaymentIntent veya bulunamazsa None.
        """

    @abstractmethod
    async def find_by_target(
        self,
        target_type: PaymentTargetType,
        target_id: uuid.UUID,
    ) -> Optional[PaymentIntent]:
        """Hedef türü ve ID ile PaymentIntent getir.

        Bir Mission veya Subscription'a ait ödeme niyetini bulmak için kullanılır.

        Args:
            target_type: Hedef türü (MISSION veya SUBSCRIPTION).
            target_id: Hedef ID'si (mission_id veya subscription_id).

        Returns:
            PaymentIntent veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_payer_user_id(
        self,
        payer_user_id: uuid.UUID,
        *,
        status: Optional[PaymentStatus] = None,
    ) -> List[PaymentIntent]:
        """Bir kullanıcının ödeme niyetlerini getir (durum filtresi opsiyonel).

        Args:
            payer_user_id: Ödemeyi yapan User ID'si.
            status: Opsiyonel durum filtresi.

        Returns:
            PaymentIntent listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_status(self, status: PaymentStatus) -> List[PaymentIntent]:
        """Belirli durumdaki tüm ödeme niyetlerini getir.

        Süre aşımı kontrolü, raporlama ve admin paneli için kullanılır.

        Args:
            status: Ödeme durumu (KR-033 kanonik durumlar).

        Returns:
            PaymentIntent listesi (boş olabilir).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, payment_intent_id: uuid.UUID) -> None:
        """PaymentIntent sil.

        Args:
            payment_intent_id: Silinecek ödeme niyeti ID'si.

        Raises:
            KeyError: payment_intent_id bulunamadığında.
        """
