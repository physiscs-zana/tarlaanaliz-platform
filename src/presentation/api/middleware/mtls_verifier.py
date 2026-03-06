# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-071: mTLS cihaz kimlik dogrulamasi.
"""mTLS verifier middleware: EdgeKiosk cihaz sertifika dogrulamasi.

KR-071: Tek yonlu veri akisi + allowlist yerlesimi (Ingress).
  - mTLS ana kimlik; allowlist ikincil.
  - EdgeKiosk → Platform/Ingress: HTTPS 443 uzerinden, mTLS cihaz kimliği ile.
  - IP allowlist sadece Ingress kapisinda ikincil katman olarak uygulanir.

KR-070: Worker izolasyonu; ingest endpoint'leri mTLS zorunlu.

Bu middleware, reverse proxy/ingress tarafindan set edilen client sertifika
header'larini dogrular. Ingest endpoint'lerinde sertifika olmadan erisim reddedilir.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Callable, cast

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.presentation.api.middleware._shared import (
    METRICS_HOOK,
    ensure_request_context,
    get_client_ip,
    mask_ip,
)

LOGGER = logging.getLogger("api.middleware.mtls_verifier")

# mTLS zorunlu endpoint prefix'leri (EdgeKiosk ingest)
_MTLS_REQUIRED_PATHS: tuple[str, ...] = (
    "/api/v1/ingest",
    "/api/v1/datasets",
    "/api/v1/transfer-batches",
)

# mTLS bypass edilecek yollar (health, docs, auth)
_BYPASS_PATHS: tuple[str, ...] = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)

# Reverse proxy'den gelen client sertifika header'lari
# (Nginx: X-SSL-Client-Cert, Envoy: X-Forwarded-Client-Cert, Traefik: X-Forwarded-Tls-Client-Cert)
_CERT_HEADERS: tuple[str, ...] = (
    "x-ssl-client-cert",
    "x-forwarded-client-cert",
    "x-forwarded-tls-client-cert",
    "x-client-cert",
)

# Sertifika verify sonucu header'i (Nginx: X-SSL-Client-Verify)
_VERIFY_HEADER = "x-ssl-client-verify"

# Sertifika DN (Distinguished Name) header'i
_DN_HEADER = "x-ssl-client-s-dn"


class MTLSVerificationError(Exception):
    """mTLS dogrulama hatasi."""


class MTLSVerifierMiddleware(BaseHTTPMiddleware):
    """KR-071 mTLS cihaz kimlik dogrulama middleware'i.

    Ingest endpoint'lerinde:
    - Client sertifikasinin varligini dogrular
    - Sertifika verify durumunu kontrol eder
    - Basarisiz denemeleri SECURITY.DENY olarak loglar
    - Kayitsiz/iptal edilmis sertifikalari reddeder

    Diger endpoint'ler icin bypass eder (mTLS zorunlu degil).
    """

    def __init__(
        self,
        app: Any,
        registered_fingerprints: frozenset[str] | None = None,
    ) -> None:
        super().__init__(app)
        # Kayitli cihaz sertifika parmak izleri (SHA-256)
        # Production'da bu bilgi config/secret store'dan yuklenir
        self._registered_fingerprints = registered_fingerprints or frozenset()

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        corr_id, _ = ensure_request_context(request)
        path = request.url.path

        # Bypass: health/docs/auth
        if any(path.startswith(bp) for bp in _BYPASS_PATHS):
            response = cast(Response, await call_next(request))
            response.headers["X-Correlation-Id"] = corr_id
            return response

        # mTLS zorunlu mu?
        requires_mtls = any(path.startswith(p) for p in _MTLS_REQUIRED_PATHS)

        if not requires_mtls:
            response = cast(Response, await call_next(request))
            response.headers["X-Correlation-Id"] = corr_id
            return response

        # mTLS dogrulama
        client_cert = self._extract_client_cert(request)
        verify_status = request.headers.get(_VERIFY_HEADER, "").upper()

        if not client_cert:
            return self._deny(
                request,
                corr_id,
                reason="missing_client_cert",
                message="mTLS client sertifikasi gereklidir (KR-071)",
            )

        if verify_status and verify_status != "SUCCESS":
            return self._deny(
                request,
                corr_id,
                reason="cert_verify_failed",
                message=f"Sertifika dogrulama basarisiz: {verify_status}",
            )

        # Sertifika parmak izi kontrolu (eger kayitli fingerprint'ler varsa)
        if self._registered_fingerprints:
            fingerprint = self._compute_fingerprint(client_cert)
            if fingerprint not in self._registered_fingerprints:
                return self._deny(
                    request,
                    corr_id,
                    reason="unregistered_cert",
                    message="Kayitsiz cihaz sertifikasi",
                )

        # mTLS basarili
        METRICS_HOOK.increment("mtls_verifier.success")
        request.state.mtls_verified = True
        request.state.client_cert_dn = request.headers.get(_DN_HEADER, "")

        response = cast(Response, await call_next(request))
        response.headers["X-Correlation-Id"] = corr_id
        return response

    @staticmethod
    def _extract_client_cert(request: Request) -> str | None:
        """Reverse proxy header'larindan client sertifika bilgisini cikarir."""
        for header in _CERT_HEADERS:
            value = request.headers.get(header)
            if value:
                return value
        return None

    @staticmethod
    def _compute_fingerprint(cert_pem: str) -> str:
        """Sertifika PEM'den SHA-256 parmak izi hesaplar."""
        # Basitleştirilmis fingerprint: PEM icerigi hash'lenir
        # Production'da ASN.1 DER parse yapilir
        clean = cert_pem.replace("-----BEGIN CERTIFICATE-----", "")
        clean = clean.replace("-----END CERTIFICATE-----", "")
        clean = clean.replace("\n", "").replace("\r", "").strip()
        return hashlib.sha256(clean.encode("utf-8")).hexdigest()

    def _deny(
        self,
        request: Request,
        corr_id: str,
        *,
        reason: str,
        message: str,
    ) -> JSONResponse:
        """mTLS dogrulama basarisiz; SECURITY.DENY logu ve 403 response."""
        client_ip = mask_ip(get_client_ip(request))

        METRICS_HOOK.increment(f"mtls_verifier.deny.{reason}")
        LOGGER.warning(
            "SECURITY.DENY",
            extra={
                "corr_id": corr_id,
                "event": "SECURITY.DENY",
                "reason": reason,
                "path": request.url.path,
                "method": request.method,
                "client_ip_masked": client_ip,
            },
        )

        return JSONResponse(
            status_code=403,
            content={
                "detail": message,
                "corr_id": corr_id,
            },
            headers={"X-Correlation-Id": corr_id},
        )
