# PATH: src/infrastructure/external/sms_gateway_adapter.py
# DESC: SMSGateway portunun adapter implementasyonu.
"""
SMSGateway adapter: SMS gönderim sağlayıcısı HTTP implementasyonu.

Provider'dan bağımsız SMS gönderim arayüzü. Pilot görev atamaları,
ödeme bildirimleri ve genel bildirimler için kullanılır.

PII: Telefon numarası loglanırken maskelenir.
Retry: Transient hatalarda exponential backoff.
Rate limit: Provider kotası aşılmamalı.
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


def _mask_phone(phone: str) -> str:
    """Telefon numarasını maskeler (PII koruma)."""
    if len(phone) < 7:
        return "***"
    return phone[:3] + "***" + phone[-4:]


class SMSGatewayAdapter(SMSGateway):
    """SMSGateway port implementasyonu.

    httpx async HTTP client ile SMS provider'a bağlanır.
    Tüm operasyonlarda retry uygulanır (SMS gönderim idempotent değildir,
    ancak transient hatalar retry edilmelidir).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.sms_api_url
        self._timeout = httpx.Timeout(settings.sms_timeout_seconds)
        self._api_key = settings.sms_api_key.get_secret_value()
        self._default_sender_id = settings.sms_sender_id

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )

    def _validate_phone(self, phone: str) -> None:
        """Telefon numarası formatını doğrular."""
        cleaned = phone.strip().replace(" ", "").replace("-", "")
        if not _PHONE_PATTERN.match(cleaned):
            raise ValueError(f"Geçersiz telefon numarası formatı: {_mask_phone(phone)}")

    @_RETRY_DECORATOR
    async def send_sms(
        self,
        *,
        phone_number: str,
        message: str,
        sender_id: Optional[str] = None,
    ) -> SmsResult:
        """Tek bir SMS mesajı gönder."""
        self._validate_phone(phone_number)
        masked = _mask_phone(phone_number)

        logger.info("sms_send_request", phone_masked=masked)

        async with self._get_client() as client:
            response = await client.post(
                "/sms/send",
                json={
                    "phone_number": phone_number,
                    "message": message,
                    "sender_id": sender_id or self._default_sender_id,
                },
            )
            response.raise_for_status()
            data = response.json()

        result = SmsResult(
            message_id=data["message_id"],
            status=SmsDeliveryStatus(data.get("status", "QUEUED")),
            phone_number_masked=masked,
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
        )

        logger.info(
            "sms_send_result",
            message_id=result.message_id,
            status=result.status.value,
            phone_masked=masked,
        )
        return result

    @_RETRY_DECORATOR
    async def send_sms_batch(
        self,
        *,
        recipients: list[str],
        message: str,
        sender_id: Optional[str] = None,
    ) -> SmsBatchResult:
        """Birden fazla alıcıya aynı mesajı gönder."""
        for phone in recipients:
            self._validate_phone(phone)

        logger.info("sms_batch_request", recipient_count=len(recipients))

        async with self._get_client() as client:
            response = await client.post(
                "/sms/send-batch",
                json={
                    "recipients": recipients,
                    "message": message,
                    "sender_id": sender_id or self._default_sender_id,
                },
            )
            response.raise_for_status()
            data = response.json()

        results = tuple(
            SmsResult(
                message_id=r["message_id"],
                status=SmsDeliveryStatus(r.get("status", "QUEUED")),
                phone_number_masked=_mask_phone(r.get("phone_number", "")),
                error_code=r.get("error_code"),
                error_message=r.get("error_message"),
            )
            for r in data.get("results", [])
        )

        batch_result = SmsBatchResult(
            total_sent=data.get("total_sent", 0),
            total_failed=data.get("total_failed", 0),
            results=results,
        )

        logger.info(
            "sms_batch_result",
            total_sent=batch_result.total_sent,
            total_failed=batch_result.total_failed,
        )
        return batch_result

    @_RETRY_DECORATOR
    async def get_delivery_status(
        self,
        message_id: str,
    ) -> SmsDeliveryStatus:
        """Gönderilen SMS'in teslim durumunu sorgula."""
        async with self._get_client() as client:
            response = await client.get(f"/sms/{message_id}/status")
            response.raise_for_status()
            data = response.json()

        return SmsDeliveryStatus(data["status"])

    async def health_check(self) -> bool:
        """SMS provider'ın erişilebilirliğini kontrol et."""
        try:
            async with self._get_client() as client:
                response = await client.get("/health")
                return response.status_code == 200
        except (httpx.HTTPError, Exception):
            logger.warning("sms_health_check_failed")
            return False
