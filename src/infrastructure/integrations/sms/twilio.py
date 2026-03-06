# PATH: src/infrastructure/integrations/sms/twilio.py
# DESC: Twilio SMS adapter.
"""
Twilio SMS adapter: Twilio REST API implementasyonu.

Amaç: SMSGateway portunun Twilio-spesifik implementasyonu.
Sorumluluk: Twilio REST API üzerinden SMS gönderim, toplu gönderim
  ve teslim durumu sorgulama. Uluslararası erişim için alternatif sağlayıcı.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (telefon numarası, mesaj metni).
  Çıktı: Port DTO'ları (SmsResult, SmsBatchResult, SmsDeliveryStatus).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; account_sid/auth_token env/secret manager üzerinden; TLS zorunlu.
  PII redaction: telefon numarası loglanırken maskelenir.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure; retry (exponential backoff).
  Twilio rate limit: 100 mesaj/saniye (varsayılan).

Observability (log fields/metrics/traces):
  latency, error_code, retries, message_sid, delivery_status, provider_name=twilio.

Testler: Contract test (port), integration test (Twilio test credentials), e2e.
Bağımlılıklar: httpx, tenacity, structlog.
Notlar/SSOT: Tek referans: tarlaanaliz_platform_tree v3.2.2 FINAL.
  Aynı kavram başka yerde tekrar edilmez.
"""

from __future__ import annotations

import re
from typing import Optional

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.core.ports.external.sms_gateway import (
    SMSGateway,
    SmsBatchResult,
    SmsDeliveryStatus,
    SmsResult,
)
from src.infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)

_RETRY_DECORATOR = retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)

_PHONE_PATTERN = re.compile(r"^\+?\d{10,15}$")

# Twilio message status -> SmsDeliveryStatus eşleşmesi
_TWILIO_STATUS_MAP: dict[str, SmsDeliveryStatus] = {
    "queued": SmsDeliveryStatus.QUEUED,
    "sending": SmsDeliveryStatus.QUEUED,
    "sent": SmsDeliveryStatus.SENT,
    "delivered": SmsDeliveryStatus.DELIVERED,
    "undelivered": SmsDeliveryStatus.FAILED,
    "failed": SmsDeliveryStatus.FAILED,
}


def _mask_phone(phone: str) -> str:
    """Telefon numarasını maskeler (PII koruma)."""
    if len(phone) < 7:
        return "***"
    return phone[:3] + "***" + phone[-4:]


class TwilioSMSAdapter(SMSGateway):
    """SMSGateway port implementasyonu (Twilio REST API).

    Twilio REST API ile uluslararası SMS gönderimi sağlar.
    httpx ile Basic Auth (account_sid:auth_token) kullanılır.

    Twilio API yanıtları JSON formatındadır. Message SID ile
    teslim durumu takip edilir.
    """

    # Twilio API base URL
    _TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._timeout = httpx.Timeout(settings.sms_timeout_seconds)
        # Twilio: sms_api_key = "account_sid:auth_token" formatında
        api_key = settings.sms_api_key.get_secret_value()
        if ":" in api_key:
            self._account_sid, self._auth_token = api_key.split(":", 1)
        else:
            self._account_sid = api_key
            self._auth_token = ""
        self._sender_id = settings.sms_sender_id
        self._base_url = settings.sms_api_url or f"{self._TWILIO_API_BASE}/Accounts/{self._account_sid}"

    def _get_client(self) -> httpx.AsyncClient:
        """Her istek için taze httpx client oluşturur (Basic Auth)."""
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            auth=(self._account_sid, self._auth_token),
        )

    def _validate_phone(self, phone: str) -> None:
        """Telefon numarası formatını doğrular."""
        cleaned = phone.strip().replace(" ", "").replace("-", "")
        if not _PHONE_PATTERN.match(cleaned):
            raise ValueError(f"Geçersiz telefon numarası formatı: {_mask_phone(phone)}")

    def _ensure_e164(self, phone: str) -> str:
        """Telefon numarasını E.164 formatına çevirir (Twilio gereksinimi)."""
        cleaned = phone.strip().replace(" ", "").replace("-", "")
        if not cleaned.startswith("+"):
            if cleaned.startswith("0") and len(cleaned) == 11:
                # Türkiye numarası: 05XX -> +905XX
                cleaned = "+90" + cleaned[1:]
            else:
                cleaned = "+" + cleaned
        return cleaned

    # ------------------------------------------------------------------
    # Tekil SMS gönderim
    # ------------------------------------------------------------------
    @_RETRY_DECORATOR
    async def send_sms(
        self,
        *,
        phone_number: str,
        message: str,
        sender_id: Optional[str] = None,
    ) -> SmsResult:
        """Tek bir SMS mesajı gönder (Twilio API)."""
        self._validate_phone(phone_number)
        masked = _mask_phone(phone_number)
        e164_number = self._ensure_e164(phone_number)

        logger.info(
            "twilio_send_request",
            phone_masked=masked,
            provider="twilio",
        )

        # Twilio Messages API: form-urlencoded
        form_data = {
            "To": e164_number,
            "From": sender_id or self._sender_id,
            "Body": message,
        }

        async with self._get_client() as client:
            response = await client.post(
                "/Messages.json",
                data=form_data,
            )
            response.raise_for_status()
            data = response.json()

        twilio_status = data.get("status", "queued")
        result = SmsResult(
            message_id=data.get("sid", ""),
            status=_TWILIO_STATUS_MAP.get(twilio_status, SmsDeliveryStatus.UNKNOWN),
            phone_number_masked=masked,
            error_code=str(data["error_code"]) if data.get("error_code") else None,
            error_message=data.get("error_message"),
        )

        logger.info(
            "twilio_send_result",
            message_id=result.message_id,
            status=result.status.value,
            phone_masked=masked,
            error_code=result.error_code,
            provider="twilio",
        )
        return result

    # ------------------------------------------------------------------
    # Toplu SMS gönderim
    # ------------------------------------------------------------------
    @_RETRY_DECORATOR
    async def send_sms_batch(
        self,
        *,
        recipients: list[str],
        message: str,
        sender_id: Optional[str] = None,
    ) -> SmsBatchResult:
        """Birden fazla alıcıya aynı mesajı gönder (Twilio API).

        Twilio'da native batch endpoint yoktur; her alıcıya ayrı istek
        gönderilir. Hata oluşan numaralar sonuçlarda FAILED olarak işaretlenir.
        """
        for phone in recipients:
            self._validate_phone(phone)

        logger.info(
            "twilio_batch_request",
            recipient_count=len(recipients),
            provider="twilio",
        )

        results: list[SmsResult] = []
        total_sent = 0
        total_failed = 0

        async with self._get_client() as client:
            for phone in recipients:
                masked = _mask_phone(phone)
                e164_number = self._ensure_e164(phone)

                try:
                    response = await client.post(
                        "/Messages.json",
                        data={
                            "To": e164_number,
                            "From": sender_id or self._sender_id,
                            "Body": message,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()

                    twilio_status = data.get("status", "queued")
                    results.append(
                        SmsResult(
                            message_id=data.get("sid", ""),
                            status=_TWILIO_STATUS_MAP.get(
                                twilio_status,
                                SmsDeliveryStatus.UNKNOWN,
                            ),
                            phone_number_masked=masked,
                            error_code=(str(data["error_code"]) if data.get("error_code") else None),
                            error_message=data.get("error_message"),
                        )
                    )
                    total_sent += 1

                except httpx.HTTPStatusError as exc:
                    logger.warning(
                        "twilio_batch_item_failed",
                        phone_masked=masked,
                        status_code=exc.response.status_code,
                        provider="twilio",
                    )
                    results.append(
                        SmsResult(
                            message_id="",
                            status=SmsDeliveryStatus.FAILED,
                            phone_number_masked=masked,
                            error_code=str(exc.response.status_code),
                            error_message="Twilio gönderim hatası",
                        )
                    )
                    total_failed += 1

        batch = SmsBatchResult(
            total_sent=total_sent,
            total_failed=total_failed,
            results=tuple(results),
        )

        logger.info(
            "twilio_batch_result",
            total_sent=batch.total_sent,
            total_failed=batch.total_failed,
            provider="twilio",
        )
        return batch

    # ------------------------------------------------------------------
    # Teslim durumu sorgulama
    # ------------------------------------------------------------------
    @_RETRY_DECORATOR
    async def get_delivery_status(
        self,
        message_id: str,
    ) -> SmsDeliveryStatus:
        """Gönderilen SMS'in teslim durumunu sorgula (Twilio API)."""
        logger.info(
            "twilio_delivery_status_request",
            message_id=message_id,
            provider="twilio",
        )

        async with self._get_client() as client:
            response = await client.get(f"/Messages/{message_id}.json")
            response.raise_for_status()
            data = response.json()

        twilio_status = data.get("status", "unknown")
        status = _TWILIO_STATUS_MAP.get(twilio_status, SmsDeliveryStatus.UNKNOWN)

        logger.info(
            "twilio_delivery_status_result",
            message_id=message_id,
            status=status.value,
            raw_status=twilio_status,
            provider="twilio",
        )
        return status

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    async def health_check(self) -> bool:
        """Twilio API erişilebilirliğini kontrol et."""
        try:
            async with self._get_client() as client:
                response = await client.get(".json")
                return response.status_code == 200
        except (httpx.HTTPError, Exception):
            logger.warning("twilio_health_check_failed", provider="twilio")
            return False
