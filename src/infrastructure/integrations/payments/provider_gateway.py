# PATH: src/infrastructure/integrations/payments/provider_gateway.py
# DESC: PaymentGateway portunun seçilen sağlayıcı implementasyonu.
"""
PaymentGateway provider implementasyonu: sağlayıcı-spesifik ödeme altyapısı.

Amaç: PaymentGateway portunun seçilen sağlayıcı (iyzico, param, stripe)
  üzerinden implementasyonu. Provider seçimi runtime konfigürasyonuna göre yapılır.

Sorumluluk: Bağlamına göre beklenen sorumlulukları yerine getirir;
  SSOT v3.2.2 ile uyumlu kalır.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (tutar, referans, para birimi).
  Çıktı: Port DTO'ları (PaymentSessionResponse, PaymentVerificationResult, RefundResult).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; API key/secret env/secret manager üzerinden; TLS zorunlu.
  Kart bilgileri asla core'da tutulmaz; tokenization provider'da yapılır.
  KR-033: PaymentIntent olmadan paid state olmaz; dekont + manuel onay + audit.

Hata Modları (idempotency/retry/rate limit):
  Ödeme başlatma retry edilmez (çift tahsilat riski).
  Sorgu/doğrulama işlemleri retry-safe (exponential backoff).
  Idempotency: payment_ref benzersizliği ile çift tahsilat önlenir.

Observability (log fields/metrics/traces):
  latency, error_code, retries, payment_ref, amount_kurus, provider_name.

Testler: Contract test (port), integration test (provider sandbox), e2e.
Bağımlılıklar: httpx, tenacity, structlog.
Notlar/SSOT: Tek referans: tarlaanaliz_platform_tree v3.2.2 FINAL.
  Aynı kavram başka yerde tekrar edilmez.
  KR-033: PaymentIntent olmadan paid state olmaz; dekont + manuel onay + audit.
"""

from __future__ import annotations

import hashlib
import hmac
import json
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


class ProviderPaymentGateway(PaymentGateway):
    """PaymentGateway port implementasyonu (KR-033, provider-spesifik).

    Runtime konfigürasyonuna göre seçilen ödeme sağlayıcısına (iyzico, param,
    stripe) bağlanır. httpx async HTTP client kullanır.

    KR-033 kuralları:
      - Ödeme başlatma (initiate) retry edilmez (çift tahsilat riski).
      - Yalnızca sorgu (verify/status/refund) işlemlerinde retry uygulanır.
      - PaymentIntent olmadan paid state olmaz.
      - Her ödeme için dekont + manuel onay + audit.

    API key ve secret, Settings üzerinden SecretStr ile yüklenir.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._provider = settings.payment_provider
        self._base_url = settings.payment_api_url
        self._timeout = httpx.Timeout(settings.payment_timeout_seconds)
        self._api_key = settings.payment_api_key.get_secret_value()
        self._secret_key = settings.payment_secret_key.get_secret_value()

    def _get_client(self) -> httpx.AsyncClient:
        """Her istek için taze httpx client oluşturur."""
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._build_auth_headers(),
        )

    def _build_auth_headers(self) -> dict[str, str]:
        """Provider'a özel auth header'ları oluşturur."""
        headers: dict[str, str] = {"Content-Type": "application/json"}

        if self._provider == "iyzico":
            headers["Authorization"] = f"IYZWS {self._api_key}"
        elif self._provider == "stripe":
            headers["Authorization"] = f"Bearer {self._api_key}"
        else:
            # param veya diğer provider'lar
            headers["Authorization"] = f"Bearer {self._api_key}"

        return headers

    def _compute_signature(self, payload: dict[str, Any]) -> str:
        """İstek imzası hesaplar (iyzico/param için gerekli)."""
        payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        return hmac.new(
            self._secret_key.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    # ------------------------------------------------------------------
    # Ödeme başlatma — RETRY YAPILMAZ (çift tahsilat riski)
    # ------------------------------------------------------------------
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
        """Ödeme oturumu başlat (KR-033). Retry YAPILMAZ."""
        if amount_kurus <= 0:
            raise ValueError(f"amount_kurus pozitif olmalıdır: {amount_kurus}")

        payload: dict[str, Any] = {
            "payment_ref": payment_ref,
            "amount_kurus": amount_kurus,
            "currency": currency,
            "provider": self._provider,
        }
        if description:
            payload["description"] = description
        if callback_url:
            payload["callback_url"] = callback_url
        if metadata:
            payload["metadata"] = metadata

        logger.info(
            "provider_payment_initiate_request",
            provider=self._provider,
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
            "provider_payment_initiate_success",
            provider=self._provider,
            payment_ref=payment_ref,
            provider_session_id=result.provider_session_id,
        )
        return result

    # ------------------------------------------------------------------
    # Doğrulama — retry güvenli
    # ------------------------------------------------------------------
    @_RETRY_DECORATOR
    async def verify_payment(
        self,
        provider_payment_id: str,
    ) -> PaymentVerificationResult:
        """Ödemenin tamamlandığını doğrula (retry destekli)."""
        logger.info(
            "provider_payment_verify_request",
            provider=self._provider,
            provider_payment_id=provider_payment_id,
        )

        async with self._get_client() as client:
            response = await client.get(f"/payments/{provider_payment_id}/verify")
            response.raise_for_status()
            data = response.json()

        result = PaymentVerificationResult(
            provider_payment_id=data["payment_id"],
            verified=data["verified"],
            status=data["status"],
            amount_kurus=data.get("amount_kurus", 0),
            currency=data.get("currency", "TRY"),
            message=data.get("message", ""),
        )

        logger.info(
            "provider_payment_verify_result",
            provider=self._provider,
            provider_payment_id=result.provider_payment_id,
            verified=result.verified,
            status=result.status,
        )
        return result

    # ------------------------------------------------------------------
    # İade — retry güvenli (KR-033 Kural-4)
    # ------------------------------------------------------------------
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
            "provider_payment_refund_request",
            provider=self._provider,
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

        result = RefundResult(
            provider_refund_id=data["refund_id"],
            success=data["success"],
            refunded_amount_kurus=data.get("refunded_amount_kurus", 0),
            message=data.get("message", ""),
        )

        logger.info(
            "provider_payment_refund_result",
            provider=self._provider,
            provider_refund_id=result.provider_refund_id,
            success=result.success,
            refunded_amount_kurus=result.refunded_amount_kurus,
        )
        return result

    # ------------------------------------------------------------------
    # Durum sorgulama — retry güvenli
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    async def health_check(self) -> bool:
        """Ödeme sağlayıcısının erişilebilirliğini kontrol et."""
        try:
            async with self._get_client() as client:
                response = await client.get("/health")
                return response.status_code == 200
        except (httpx.HTTPError, Exception):
            logger.warning(
                "provider_payment_health_check_failed",
                provider=self._provider,
            )
            return False
