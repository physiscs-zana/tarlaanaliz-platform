# PATH: src/core/ports/external/payment_gateway.py
# DESC: PaymentGateway portu: kartlı ödeme sağlayıcısı.
# SSOT: KR-033 (ödeme ve manuel onay)
"""
PaymentGateway portu: kartlı ödeme sağlayıcısı.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  Ödeme sağlayıcısı (iyzico, param, stripe vb.) ile iletişimi soyutlar.
  PaymentIntent oluşturma, ödeme doğrulama ve iade işlemlerini kapsar.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (tutar, para birimi, referans ID).
  Çıktı: IO sonuçları (provider session, ödeme durumu, iade onayı).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: kart bilgileri asla core'da tutulmaz; tokenization provider'da.
  KR-033: PaymentIntent olmadan paid state olmaz; dekont + manuel onay + audit.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel). Ödeme işlemlerinde çift tahsilat önleme kritik.

Observability (log fields/metrics/traces):
  latency, error_code, retries, payment_ref, amount_kurus, provider_response_code.

Testler: Contract test (port), integration test (provider sandbox), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon (_impl) taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
  KR-033: PaymentIntent olmadan paid state olmaz; dekont + manuel onay + audit.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


# ------------------------------------------------------------------
# Port-specific DTOs (Contract nesneleri)
# ------------------------------------------------------------------
@dataclass(frozen=True)
class PaymentSessionResponse:
    """Ödeme sağlayıcısından dönen oturum bilgisi.

    Provider'ın oluşturduğu ödeme sayfası ve referansları.
    PII (kart bilgisi) bu DTO'da bulunmaz; provider tarafında tokenize edilir.
    """

    provider_session_id: str
    checkout_url: str
    expires_at: Optional[str] = None  # ISO-8601
    provider_metadata: Optional[dict[str, Any]] = None


@dataclass(frozen=True)
class PaymentVerificationResult:
    """Ödeme doğrulama sonucu.

    Sağlayıcıdan alınan nihai ödeme durumunu temsil eder.
    """

    provider_payment_id: str
    verified: bool
    status: str  # COMPLETED | PENDING | FAILED | CANCELLED
    amount_kurus: int = 0
    currency: str = "TRY"
    message: str = ""


@dataclass(frozen=True)
class RefundResult:
    """İade işlemi sonucu."""

    provider_refund_id: str
    success: bool
    refunded_amount_kurus: int = 0
    message: str = ""


# ------------------------------------------------------------------
# Port Interface
# ------------------------------------------------------------------
class PaymentGateway(ABC):
    """Payment Gateway portu (KR-033).

    Kartlı ödeme sağlayıcısı ile iletişimi soyutlar.
    PaymentIntent entity'si ile birlikte çalışır.

    Infrastructure katmanı bu interface'i implemente eder:
      - iyzico / param / stripe SDK wrapper
      - Webhook handler altyapısı (ayrı adapter)

    Idempotency: payment_ref benzersizliği ile çift tahsilat önlenir.
    Retry: Yalnızca sorgu (verify/status) işlemlerinde retry uygulanır;
           ödeme başlatma (initiate) retry edilmez (çift tahsilat riski).
    """

    # ------------------------------------------------------------------
    # Ödeme başlatma
    # ------------------------------------------------------------------
    @abstractmethod
    async def initiate_payment(
        self,
        *,
        payment_intent_id: uuid.UUID,
        payment_ref: str,
        amount_kurus: int,
        currency: str,
        description: Optional[str] = None,
        callback_url: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> PaymentSessionResponse:
        """Ödeme oturumu başlat (KR-033).

        Provider'da ödeme sayfası oluşturur ve yönlendirme URL'i döner.
        Bu metot retry edilmemelidir (çift tahsilat riski).

        Args:
            payment_intent_id: İlişkili PaymentIntent ID'si.
            payment_ref: Benzersiz ödeme referansı (PAY-YYYYMMDD-XXXXXX).
            amount_kurus: Kuruş cinsinden tutar (positive).
            currency: Para birimi kodu (TRY).
            description: Ödeme açıklaması.
            callback_url: Ödeme sonrası yönlendirme URL'i.
            metadata: Provider'a iletilecek ek bilgiler.

        Returns:
            PaymentSessionResponse: Provider session bilgileri.

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
            ValueError: Geçersiz tutar veya para birimi.
        """

    # ------------------------------------------------------------------
    # Ödeme doğrulama
    # ------------------------------------------------------------------
    @abstractmethod
    async def verify_payment(
        self,
        provider_payment_id: str,
    ) -> PaymentVerificationResult:
        """Ödemenin tamamlandığını doğrula (KR-033).

        Provider webhook'undan sonra veya polling ile çağrılır.

        Args:
            provider_payment_id: Provider tarafından atanan ödeme ID'si.

        Returns:
            PaymentVerificationResult: Nihai ödeme durumu.

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
            KeyError: provider_payment_id bulunamadığında.
        """

    # ------------------------------------------------------------------
    # İade
    # ------------------------------------------------------------------
    @abstractmethod
    async def refund_payment(
        self,
        *,
        provider_payment_id: str,
        refund_amount_kurus: int,
        reason: str,
    ) -> RefundResult:
        """Ödeme iadesi başlat (KR-033 Kural-4).

        Yalnızca PAID durumundaki ödemeler için çağrılır.
        Kısmi iade desteklenir.

        Args:
            provider_payment_id: İade edilecek ödemenin provider ID'si.
            refund_amount_kurus: İade tutarı (kuruş, ≤ orijinal tutar).
            reason: İade gerekçesi (audit için).

        Returns:
            RefundResult: İade işlemi sonucu.

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
            ValueError: Geçersiz iade tutarı.
        """

    # ------------------------------------------------------------------
    # Durum sorgulama
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_payment_status(
        self,
        provider_payment_id: str,
    ) -> PaymentVerificationResult:
        """Provider'dan güncel ödeme durumunu sorgula.

        Args:
            provider_payment_id: Sorgulanacak ödemenin provider ID'si.

        Returns:
            PaymentVerificationResult: Güncel durum.

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    @abstractmethod
    async def health_check(self) -> bool:
        """Ödeme sağlayıcısının erişilebilirliğini kontrol et.

        Returns:
            True: Servis sağlıklı ve erişilebilir.
            False: Servis erişilemez veya hata durumunda.
        """
