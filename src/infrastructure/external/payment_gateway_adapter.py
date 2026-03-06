# PATH: src/infrastructure/external/payment_gateway_adapter.py
# DESC: PaymentGateway portunun adapter implementasyonu.
"""
PaymentGateway adapter: kartlı ödeme sağlayıcısı HTTP implementasyonu.

KR-033: PaymentIntent olmadan paid state olmaz; dekont + manuel onay + audit.
Ödeme başlatma (initiate) retry edilmez (çift tahsilat riski).
Yalnızca sorgu (verify/status) işlemlerinde retry uygulanır.

Desteklenen provider'lar: iyzico, param, stripe (provider config ile belirlenir).
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.core.ports.external.payment_gateway import (
    PaymentGateway,
    PaymentSessionResponse,
    PaymentVerificationResult,
    RefundResult,
)
from src.infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)

_RETRY_DECORATOR = retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)


class PaymentGatewayAdapter(PaymentGateway):
    """PaymentGateway port implementasyonu (KR-033).

    httpx async HTTP client ile ödeme sağlayıcısına bağlanır.
    Ödeme başlatma retry edilmez; doğrulama ve sorguda retry uygulanır.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.payment_api_url
        self._timeout = httpx.Timeout(settings.payment_timeout_seconds)
        self._api_key = settings.payment_api_key.get_secret_value()
        self._secret_key = settings.payment_secret_key.get_secret_value()

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )

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
        """Ödeme oturumu başlat. Retry YAPILMAZ (çift tahsilat riski)."""
        if amount_kurus <= 0:
            raise ValueError(f"amount_kurus pozitif olmalıdır: {amount_kurus}")

        payload: dict[str, Any] = {
            "payment_ref": payment_ref,
            "amount_kurus": amount_kurus,
            "currency": currency,
        }
        if description:
            payload["description"] = description
        if callback_url:
            payload["callback_url"] = callback_url
        if metadata:
            payload["metadata"] = metadata

        logger.info(
            "payment_initiate_request",
            payment_intent_id=str(payment_intent_id),
            payment_ref=payment_ref,
            amount_kurus=amount_kurus,
            currency=currency,
        )

        async with self._get_client() as client:
            response = await client.post("/payments/initiate", json=payload)
            response.raise_for_status()
            data = response.json()

        result = PaymentSessionResponse(
            provider_session_id=data["session_id"],
            checkout_url=data["checkout_url"],
            expires_at=data.get("expires_at"),
            provider_metadata=data.get("metadata"),
        )

        logger.info(
            "payment_initiate_success",
            payment_ref=payment_ref,
            provider_session_id=result.provider_session_id,
        )
        return result

    @_RETRY_DECORATOR
    async def verify_payment(
        self,
        provider_payment_id: str,
    ) -> PaymentVerificationResult:
        """Ödemenin tamamlandığını doğrula (retry destekli)."""
        logger.info("payment_verify_request", provider_payment_id=provider_payment_id)

        async with self._get_client() as client:
            response = await client.get(f"/payments/{provider_payment_id}/verify")
            response.raise_for_status()
            data = response.json()

        return PaymentVerificationResult(
            provider_payment_id=data["payment_id"],
            verified=data["verified"],
            status=data["status"],
            amount_kurus=data.get("amount_kurus", 0),
            currency=data.get("currency", "TRY"),
            message=data.get("message", ""),
        )

    @_RETRY_DECORATOR
    async def refund_payment(
        self,
        *,
        provider_payment_id: str,
        refund_amount_kurus: int,
        reason: str,
    ) -> RefundResult:
        """Ödeme iadesi başlat (KR-033 Kural-4)."""
        if refund_amount_kurus <= 0:
            raise ValueError(f"refund_amount_kurus pozitif olmalıdır: {refund_amount_kurus}")

        logger.info(
            "payment_refund_request",
            provider_payment_id=provider_payment_id,
            refund_amount_kurus=refund_amount_kurus,
        )

        async with self._get_client() as client:
            response = await client.post(
                f"/payments/{provider_payment_id}/refund",
                json={
                    "amount_kurus": refund_amount_kurus,
                    "reason": reason,
                },
            )
            response.raise_for_status()
            data = response.json()

        return RefundResult(
            provider_refund_id=data["refund_id"],
            success=data["success"],
            refunded_amount_kurus=data.get("refunded_amount_kurus", 0),
            message=data.get("message", ""),
        )

    @_RETRY_DECORATOR
    async def get_payment_status(
        self,
        provider_payment_id: str,
    ) -> PaymentVerificationResult:
        """Provider'dan güncel ödeme durumunu sorgula (retry destekli)."""
        async with self._get_client() as client:
            response = await client.get(f"/payments/{provider_payment_id}/status")
            response.raise_for_status()
            data = response.json()

        return PaymentVerificationResult(
            provider_payment_id=data["payment_id"],
            verified=data.get("verified", False),
            status=data["status"],
            amount_kurus=data.get("amount_kurus", 0),
            currency=data.get("currency", "TRY"),
            message=data.get("message", ""),
        )

    async def health_check(self) -> bool:
        """Ödeme sağlayıcısının erişilebilirliğini kontrol et."""
        try:
            async with self._get_client() as client:
                response = await client.get("/health")
                return response.status_code == 200
        except (httpx.HTTPError, Exception):
            logger.warning("payment_health_check_failed")
            return False
