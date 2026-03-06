# PATH: src/core/ports/external/sms_gateway.py
# DESC: SMSGateway portu: SMS gönderimi provider'dan bağımsız.
# SSOT: KR-015 (görev bildirimleri), KR-033 (ödeme bildirimleri)
"""
SMSGateway portu: SMS gönderimi provider'dan bağımsız.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  SMS gönderim sağlayıcısını (NetGSM, Twilio, vb.) soyutlar.
  Pilot bildirimleri, ödeme uyarıları, OTP doğrulama için kullanılır.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (telefon numarası, mesaj metni).
  Çıktı: IO sonuçları (gönderim onayı, teslim durumu).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: telefon numarası PII'dır; loglanırken maskelenir.
  Telefon numarası yalnızca SMS gönderimi için kullanılır, saklanmaz.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel). Rate limit: provider kotası aşılmamalı.

Observability (log fields/metrics/traces):
  latency, error_code, retries, message_id, delivery_status, provider_name.

Testler: Contract test (port), integration test (provider sandbox), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon (_impl) taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ------------------------------------------------------------------
# Port-specific DTOs (Contract nesneleri)
# ------------------------------------------------------------------
class SmsDeliveryStatus(str, Enum):
    """SMS teslim durumu."""

    QUEUED = "QUEUED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SmsResult:
    """Tek SMS gönderim sonucu.

    PII: phone_number_masked alanı maskelenmiş halde sunulur (log için).
    """

    message_id: str
    status: SmsDeliveryStatus
    phone_number_masked: str = ""  # ör: +90***1234
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass(frozen=True)
class SmsBatchResult:
    """Toplu SMS gönderim sonucu."""

    total_sent: int
    total_failed: int
    results: tuple[SmsResult, ...] = ()


# ------------------------------------------------------------------
# Port Interface
# ------------------------------------------------------------------
class SMSGateway(ABC):
    """SMS Gateway portu.

    Provider'dan bağımsız SMS gönderim arayüzü. Pilot görev atamaları,
    ödeme bildirimleri, OTP doğrulama ve genel bildirimler için kullanılır.

    Infrastructure katmanı bu interface'i implemente eder:
      - NetGSM API wrapper
      - Twilio SDK wrapper
      - Mock/test provider

    Idempotency: message_id ile tekrar gönderim takibi yapılabilir.
    Retry: Transient hatalarda exponential backoff ile yeniden denenir.
    Rate limit: Provider kotasına dikkat; burst gönderim için batch tercih edilir.
    """

    # ------------------------------------------------------------------
    # Tekil SMS gönderim
    # ------------------------------------------------------------------
    @abstractmethod
    async def send_sms(
        self,
        *,
        phone_number: str,
        message: str,
        sender_id: Optional[str] = None,
    ) -> SmsResult:
        """Tek bir SMS mesajı gönder.

        Args:
            phone_number: Alıcı telefon numarası (uluslararası format, +90...).
            message: Mesaj metni (provider karakter limitlerine tabidir).
            sender_id: Gönderici başlığı (opsiyonel; provider varsayılanı kullanılır).

        Returns:
            SmsResult: Gönderim sonucu (message_id, status).

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
            ValueError: Geçersiz telefon numarası formatı.
        """

    # ------------------------------------------------------------------
    # Toplu SMS gönderim
    # ------------------------------------------------------------------
    @abstractmethod
    async def send_sms_batch(
        self,
        *,
        recipients: list[str],
        message: str,
        sender_id: Optional[str] = None,
    ) -> SmsBatchResult:
        """Birden fazla alıcıya aynı mesajı gönder.

        Args:
            recipients: Alıcı telefon numaraları listesi.
            message: Mesaj metni.
            sender_id: Gönderici başlığı (opsiyonel).

        Returns:
            SmsBatchResult: Toplu gönderim sonuçları.

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Teslim durumu sorgulama
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_delivery_status(
        self,
        message_id: str,
    ) -> SmsDeliveryStatus:
        """Gönderilen SMS'in teslim durumunu sorgula.

        Args:
            message_id: send_sms'ten dönen mesaj ID'si.

        Returns:
            SmsDeliveryStatus: Güncel teslim durumu.

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            KeyError: message_id bulunamadığında.
        """

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    @abstractmethod
    async def health_check(self) -> bool:
        """SMS provider'ın erişilebilirliğini kontrol et.

        Returns:
            True: Servis sağlıklı ve erişilebilir.
            False: Servis erişilemez veya hata durumunda.
        """
