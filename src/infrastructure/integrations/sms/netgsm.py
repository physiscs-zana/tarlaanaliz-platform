# PATH: src/infrastructure/integrations/sms/netgsm.py
# DESC: NetGSM SMS adapter.
"""
NetGSM SMS adapter: NetGSM API implementasyonu.

Amaç: SMSGateway portunun NetGSM-spesifik implementasyonu.
Sorumluluk: NetGSM REST API üzerinden SMS gönderim, toplu gönderim
  ve teslim durumu sorgulama. Türkiye pazarı için birincil SMS sağlayıcı.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (telefon numarası, mesaj metni).
  Çıktı: Port DTO'ları (SmsResult, SmsBatchResult, SmsDeliveryStatus).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; API usercode/password env/secret manager üzerinden; TLS zorunlu.
  PII redaction: telefon numarası loglanırken maskelenir.
  Telefon numarası yalnızca SMS gönderimi için kullanılır, saklanmaz.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure; retry (exponential backoff).
  NetGSM rate limit: dakikada 100 istek. Burst gönderimde batch tercih edilir.

Observability (log fields/metrics/traces):
  latency, error_code, retries, message_id, delivery_status, provider_name=netgsm.

Testler: Contract test (port), integration test (NetGSM sandbox), e2e.
Bağımlılıklar: httpx, tenacity, structlog.
Notlar/SSOT: Tek referans: tarlaanaliz_platform_tree v3.2.2 FINAL.
  Aynı kavram başka yerde tekrar edilmez.
"""

from __future__ import annotations

import re
from typing import Optional
from xml.sax.saxutils import escape as xml_escape

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

# NetGSM API hata kodları -> SmsDeliveryStatus eşleşmesi
_NETGSM_STATUS_MAP: dict[str, SmsDeliveryStatus] = {
    "00": SmsDeliveryStatus.QUEUED,  # Başarılı, kuyruğa alındı
    "01": SmsDeliveryStatus.SENT,  # Operatöre iletildi
    "02": SmsDeliveryStatus.DELIVERED,  # Teslim edildi
    "03": SmsDeliveryStatus.FAILED,  # Hata (geçersiz numara vb.)
}

# NetGSM API hata kodları (send response)
_NETGSM_ERROR_CODES: dict[str, str] = {
    "20": "Mesaj metninde hata var",
    "30": "Geçersiz kullanıcı adı/şifre",
    "40": "Mesaj başlığı tanımsız",
    "50": "Abone olmayan hedef numara",
    "51": "Yetersiz bakiye",
    "70": "Parametre hatası",
    "80": "Sorgu limiti aşıldı",
    "85": "Mükerrer gönderim (aynı mesaj kısa sürede tekrar)",
}


def _mask_phone(phone: str) -> str:
    """Telefon numarasını maskeler (PII koruma)."""
    if len(phone) < 7:
        return "***"
    return phone[:3] + "***" + phone[-4:]


def _normalize_phone(phone: str) -> str:
    """Telefon numarasını NetGSM formatına çevirir (başında 0 olmadan, 10 hane)."""
    cleaned = phone.strip().replace(" ", "").replace("-", "")
    if cleaned.startswith("+90"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("0090"):
        cleaned = cleaned[4:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]
    return cleaned


class NetGSMAdapter(SMSGateway):
    """SMSGateway port implementasyonu (NetGSM API).

    NetGSM REST/XML API ile Türkiye'ye SMS gönderimi sağlar.
    Tüm gönderim operasyonlarında retry uygulanır.

    API usercode, password ve başlık bilgisi Settings üzerinden yüklenir.
    NetGSM API XML tabanlı yanıt döner; JSON endpoint kullanılabiliyorsa
    tercih edilir.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.sms_api_url or "https://api.netgsm.com.tr"
        self._timeout = httpx.Timeout(settings.sms_timeout_seconds)
        self._api_key = settings.sms_api_key.get_secret_value()
        self._sender_id = settings.sms_sender_id

    def _get_client(self) -> httpx.AsyncClient:
        """Her istek için taze httpx client oluşturur."""
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={
                "Authorization": f"Basic {self._api_key}",
                "Content-Type": "application/xml",
            },
        )

    def _validate_phone(self, phone: str) -> None:
        """Telefon numarası formatını doğrular."""
        cleaned = phone.strip().replace(" ", "").replace("-", "")
        if not _PHONE_PATTERN.match(cleaned):
            raise ValueError(f"Geçersiz telefon numarası formatı: {_mask_phone(phone)}")

    def _parse_send_response(self, response_text: str, phone_masked: str) -> SmsResult:
        """NetGSM gönderim yanıtını parse eder."""
        text = response_text.strip()

        # NetGSM başarılı yanıt: "00 <bulk_id>" veya sadece hata kodu
        parts = text.split(" ", 1)
        code = parts[0]

        if code == "00":
            message_id = parts[1] if len(parts) > 1 else code
            return SmsResult(
                message_id=message_id,
                status=SmsDeliveryStatus.QUEUED,
                phone_number_masked=phone_masked,
            )

        error_msg = _NETGSM_ERROR_CODES.get(code, f"Bilinmeyen hata kodu: {code}")
        return SmsResult(
            message_id="",
            status=SmsDeliveryStatus.FAILED,
            phone_number_masked=phone_masked,
            error_code=code,
            error_message=error_msg,
        )

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
        """Tek bir SMS mesajı gönder (NetGSM API)."""
        self._validate_phone(phone_number)
        masked = _mask_phone(phone_number)
        normalized = _normalize_phone(phone_number)

        logger.info(
            "netgsm_send_request",
            phone_masked=masked,
            provider="netgsm",
        )

        # NetGSM XML payload (xml_escape prevents XML injection in header/body fields)
        safe_header = xml_escape(sender_id or self._sender_id)
        xml_payload = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<mainbody>"
            "<header>"
            f"<msgheader>{safe_header}</msgheader>"
            "</header>"
            "<body>"
            f"<msg><![CDATA[{message}]]></msg>"
            f"<no>{xml_escape(normalized)}</no>"
            "</body>"
            "</mainbody>"
        )

        async with self._get_client() as client:
            response = await client.post(
                "/sms/send/get",
                content=xml_payload.encode("utf-8"),
            )
            response.raise_for_status()

        result = self._parse_send_response(response.text, masked)

        logger.info(
            "netgsm_send_result",
            message_id=result.message_id,
            status=result.status.value,
            phone_masked=masked,
            error_code=result.error_code,
            provider="netgsm",
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
        """Birden fazla alıcıya aynı mesajı gönder (NetGSM API)."""
        for phone in recipients:
            self._validate_phone(phone)

        logger.info(
            "netgsm_batch_request",
            recipient_count=len(recipients),
            provider="netgsm",
        )

        normalized_numbers = [_normalize_phone(p) for p in recipients]
        numbers_xml = "".join(f"<no>{xml_escape(n)}</no>" for n in normalized_numbers)
        safe_header = xml_escape(sender_id or self._sender_id)

        xml_payload = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<mainbody>"
            "<header>"
            f"<msgheader>{safe_header}</msgheader>"
            "</header>"
            "<body>"
            f"<msg><![CDATA[{message}]]></msg>"
            f"{numbers_xml}"
            "</body>"
            "</mainbody>"
        )

        async with self._get_client() as client:
            response = await client.post(
                "/sms/send/get",
                content=xml_payload.encode("utf-8"),
            )
            response.raise_for_status()

        text = response.text.strip()
        parts = text.split(" ", 1)
        code = parts[0]
        bulk_id = parts[1] if len(parts) > 1 else ""

        if code == "00":
            results = tuple(
                SmsResult(
                    message_id=f"{bulk_id}-{i}",
                    status=SmsDeliveryStatus.QUEUED,
                    phone_number_masked=_mask_phone(recipients[i]),
                )
                for i in range(len(recipients))
            )
            batch = SmsBatchResult(
                total_sent=len(recipients),
                total_failed=0,
                results=results,
            )
        else:
            error_msg = _NETGSM_ERROR_CODES.get(code, f"Bilinmeyen hata kodu: {code}")
            results = tuple(
                SmsResult(
                    message_id="",
                    status=SmsDeliveryStatus.FAILED,
                    phone_number_masked=_mask_phone(recipients[i]),
                    error_code=code,
                    error_message=error_msg,
                )
                for i in range(len(recipients))
            )
            batch = SmsBatchResult(
                total_sent=0,
                total_failed=len(recipients),
                results=results,
            )

        logger.info(
            "netgsm_batch_result",
            total_sent=batch.total_sent,
            total_failed=batch.total_failed,
            provider="netgsm",
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
        """Gönderilen SMS'in teslim durumunu sorgula (NetGSM API)."""
        logger.info(
            "netgsm_delivery_status_request",
            message_id=message_id,
            provider="netgsm",
        )

        async with self._get_client() as client:
            response = await client.get(
                "/sms/report",
                params={"bulkid": message_id, "type": "0"},
            )
            response.raise_for_status()

        text = response.text.strip()
        status = _NETGSM_STATUS_MAP.get(text, SmsDeliveryStatus.UNKNOWN)

        logger.info(
            "netgsm_delivery_status_result",
            message_id=message_id,
            status=status.value,
            raw_code=text,
            provider="netgsm",
        )
        return status

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    async def health_check(self) -> bool:
        """NetGSM API erişilebilirliğini kontrol et."""
        try:
            async with self._get_client() as client:
                response = await client.get("/sms/balance")
                return response.status_code == 200
        except (httpx.HTTPError, Exception):
            logger.warning("netgsm_health_check_failed", provider="netgsm")
            return False
