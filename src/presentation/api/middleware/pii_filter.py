# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-066: KVKK PII filtreleme; KR-083: il operatoru PII goremez.
"""PII filtering middleware: response body'den PII alanlarini role-based maskeleme.

KR-066: PII ayri veri alaninda tutulur; raporlama ve KPI katmani
        pseudonymous kimliklerle calisir.
KR-083: Il operatoru PII GOREMEZ; sadece SubscriberRef + ilce veya 1-2 km grid.

Bu middleware, JSON response body'lerdeki PII alanlarini kullanici
rolune gore maskeler veya kaldırir.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, cast

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from src.presentation.api.middleware._shared import (
    METRICS_HOOK,
    ensure_request_context,
)

LOGGER = logging.getLogger("api.middleware.pii_filter")

# PII alan adlari — bu alanlar maskelenir veya kaldirilir
# SEC-FIX: GPS, pin, pin_hash alanları PII setine eklendi
PII_FIELDS: frozenset[str] = frozenset(
    {
        "phone",
        "phone_number",
        "telefon",
        "tc_kimlik_no",
        "tckn",
        "national_id",
        "iban",
        "email",
        "e_posta",
        "full_name",
        "ad_soyad",
        "address",
        "adres",
        "gps_lat",
        "gps_lon",
        "gps_latitude",
        "gps_longitude",
        "latitude",
        "longitude",
        "pin",
        "pin_hash",
        # SEC-FIX: field_id GPS lokasyon proxy'si — KR-071 uyumu
        "field_id",
    }
)

# PII icermesi BEKLENEN endpoint prefix'leri (bypass edilmez)
_ADMIN_ONLY_PATHS: frozenset[str] = frozenset(
    {
        "/api/v1/admin/users",
    }
)

# Endpoint'ler — sirket bilgisi icerdikleri icin PII filtresinden muaf
_PII_BYPASS_PATHS: frozenset[str] = frozenset(
    {
        "/api/v1/payments/methods",
        "/api/v1/pricing/crops",
        "/api/v1/admin/pricing/config",
    }
)

# PII gormeye yetkili roller (KR-063: CENTRAL_ADMIN)
_PII_ALLOWED_ROLES: frozenset[str] = frozenset(
    {
        "CENTRAL_ADMIN",
    }
)

# Telefon numarasi regex (Turkiye: 05xx xxx xx xx)
_PHONE_PATTERN = re.compile(r"0[5]\d{2}\s?\d{3}\s?\d{2}\s?\d{2}")


def _mask_value(value: str) -> str:
    """Deger maskeleme: ilk 2 ve son 2 karakter gosterilir."""
    if len(value) <= 4:
        return "***"
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def _redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Dict icerisindeki PII alanlarini maskeler."""
    redacted: dict[str, Any] = {}
    for key, value in data.items():
        lower_key = key.lower()
        if lower_key in PII_FIELDS:
            if isinstance(value, str):
                redacted[key] = _mask_value(value)
            else:
                redacted[key] = "***"
        elif isinstance(value, str) and _PHONE_PATTERN.search(value):
            redacted[key] = _PHONE_PATTERN.sub("05XX XXX XX XX", value)
        elif isinstance(value, dict):
            redacted[key] = _redact_dict(value)
        elif isinstance(value, list):
            redacted[key] = [_redact_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            redacted[key] = value
    return redacted


class PIIFilterMiddleware(BaseHTTPMiddleware):
    """KVKK PII filtreleme middleware'i.

    JSON response body'lerdeki PII alanlarini kullanici rolune gore
    maskeler. CENTRAL_ADMIN rolu haric tum roller icin PII maskelenir.
    """

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        corr_id, _ = ensure_request_context(request)

        response = cast(Response, await call_next(request))

        # Yalnizca JSON response'lari filtrele
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            response.headers["X-Correlation-Id"] = corr_id
            return response

        # Kullanici rolunu kontrol et
        # Roles are stored on request.state.roles (set by JwtMiddleware),
        # NOT on request.state.user (AuthenticatedUser has no roles attr).
        user_roles: set[str] = set(getattr(request.state, "roles", []))

        # PII gormeye yetkili roller bypass
        if user_roles & _PII_ALLOWED_ROLES:
            response.headers["X-Correlation-Id"] = corr_id
            return response

        # Sirket bilgisi iceren endpoint'ler PII filtresinden muaf
        if request.url.path in _PII_BYPASS_PATHS:
            response.headers["X-Correlation-Id"] = corr_id
            return response

        # Response body'yi oku ve PII maskele
        try:
            body = b""
            async for chunk in response.body_iterator:  # type: ignore[attr-defined]
                if isinstance(chunk, bytes):
                    body += chunk
                else:
                    body += chunk.encode("utf-8")

            data = json.loads(body)

            if isinstance(data, dict):
                data = _redact_dict(data)
            elif isinstance(data, list):
                data = [_redact_dict(item) if isinstance(item, dict) else item for item in data]

            redacted_body = json.dumps(data, ensure_ascii=False).encode("utf-8")

            METRICS_HOOK.increment("pii_filter.redacted")
            LOGGER.info(
                "pii_filter.applied",
                extra={
                    "corr_id": corr_id,
                    "path": request.url.path,
                    "role_count": len(user_roles),
                },
            )

            headers = dict(response.headers)
            headers["content-length"] = str(len(redacted_body))
            headers["X-Correlation-Id"] = corr_id

            return Response(
                content=redacted_body,
                status_code=response.status_code,
                headers=headers,
                media_type="application/json",
            )

        except (json.JSONDecodeError, UnicodeDecodeError):
            # JSON parse edilemezse orijinal response'u dondur
            response.headers["X-Correlation-Id"] = corr_id
            return response
