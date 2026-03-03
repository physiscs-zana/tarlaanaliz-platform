# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
# KR-083: Il operatoru koordinat anonimizasyonu.
"""Grid anonymizer middleware: konum verisini role-based anonimize etme.

KR-083: Il Operatoru PII GOREMEZ; sunumu iki katmanli:
  (A) Merkez — PII ayri
  (B) Operatoru — SubscriberRef + ilce veya 1-2 km grid

Bu middleware, IL_OPERATOR (ProvinceOperator) rolu icin JSON response'lardaki
koordinatlari 1-2 km grid hucresine yuvarlar ve FieldID'yi pseudonymous
FieldRef ile degistirir.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.presentation.api.middleware._shared import (
    METRICS_HOOK,
    ensure_request_context,
)

LOGGER = logging.getLogger("api.middleware.grid_anonymizer")

# Grid hucre boyutu (derece cinsinden ~1-2 km)
# Turkiye enleminde ~0.01 derece ≈ ~1.1 km
_GRID_PRECISION_DEG = 0.015

# Anonimizasyon uygulanacak roller
_ANONYMIZE_ROLES: frozenset[str] = frozenset({
    "IL_OPERATOR",
    "PROVINCE_OPERATOR",
})

# Koordinat alan adlari
_COORD_FIELDS: frozenset[str] = frozenset({
    "latitude",
    "longitude",
    "lat",
    "lng",
    "lon",
    "enlem",
    "boylam",
})

# FieldID alan adlari (pseudonymous ref ile degistirilecek)
_FIELD_ID_FIELDS: frozenset[str] = frozenset({
    "field_id",
    "fieldid",
    "tarla_id",
})

# PII alan adlari (tamamen kaldirilacak)
_STRIP_FIELDS: frozenset[str] = frozenset({
    "farmer_name",
    "farmer_phone",
    "phone",
    "phone_number",
    "full_name",
    "ad_soyad",
})


def _snap_to_grid(value: float) -> float:
    """Koordinati grid hucresine yuvarlar (~1-2 km hassasiyet)."""
    return math.floor(value / _GRID_PRECISION_DEG) * _GRID_PRECISION_DEG


def _pseudonymize_field_id(field_id: str) -> str:
    """FieldID'yi pseudonymous FieldRef'e donusturur.

    Deterministik hash; ayni FieldID her zaman ayni ref uretir.
    IL_OPERATOR icin yeterli; tam PII vault disinda.
    """
    digest = hashlib.sha256(field_id.encode("utf-8")).hexdigest()[:12]
    return f"FR-{digest.upper()}"


def _anonymize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Dict icerisindeki koordinatlari anonimize eder."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        lower_key = key.lower()

        # Koordinat alanlari: grid'e yuvarla
        if lower_key in _COORD_FIELDS and isinstance(value, (int, float)):
            result[key] = round(_snap_to_grid(float(value)), 6)
        # FieldID alanlari: pseudonymous ref
        elif lower_key in _FIELD_ID_FIELDS and isinstance(value, str):
            result[key] = _pseudonymize_field_id(value)
        # PII alanlari: tamamen kaldir
        elif lower_key in _STRIP_FIELDS:
            continue
        # Nested dict
        elif isinstance(value, dict):
            result[key] = _anonymize_dict(value)
        # Nested list
        elif isinstance(value, list):
            result[key] = [
                _anonymize_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


class GridAnonymizerMiddleware(BaseHTTPMiddleware):
    """KR-083 grid anonimizasyon middleware'i.

    IL_OPERATOR rolune sahip kullanicilar icin:
    - Koordinatlar 1-2 km grid hucresine yuvarlanir
    - FieldID, pseudonymous FieldRef ile degistirilir
    - Ciftci adi/telefonu response'dan cikarilir
    - Aggregate KPI verileri korunur
    """

    async def dispatch(
        self, request: Request, call_next: Callable[..., Any]
    ) -> Response:
        corr_id, _ = ensure_request_context(request)

        response = await call_next(request)

        # Yalnizca JSON response'lari filtrele
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            response.headers["X-Correlation-Id"] = corr_id
            return response

        # Kullanici rolunu kontrol et
        user = getattr(request.state, "user", None)
        user_roles: set[str] = set()
        if user is not None:
            user_roles = set(getattr(user, "roles", []))

        # Anonimizasyon gerekli mi?
        if not (user_roles & _ANONYMIZE_ROLES):
            response.headers["X-Correlation-Id"] = corr_id
            return response

        # Response body'yi oku ve anonimize et
        try:
            body = b""
            async for chunk in response.body_iterator:  # type: ignore[attr-defined]
                if isinstance(chunk, bytes):
                    body += chunk
                else:
                    body += chunk.encode("utf-8")

            data = json.loads(body)

            if isinstance(data, dict):
                data = _anonymize_dict(data)
            elif isinstance(data, list):
                data = [
                    _anonymize_dict(item) if isinstance(item, dict) else item
                    for item in data
                ]

            anon_body = json.dumps(data, ensure_ascii=False).encode("utf-8")

            METRICS_HOOK.increment("grid_anonymizer.applied")
            LOGGER.info(
                "grid_anonymizer.applied",
                extra={
                    "corr_id": corr_id,
                    "path": request.url.path,
                },
            )

            headers = dict(response.headers)
            headers["content-length"] = str(len(anon_body))
            headers["X-Correlation-Id"] = corr_id

            return Response(
                content=anon_body,
                status_code=response.status_code,
                headers=headers,
                media_type="application/json",
            )

        except (json.JSONDecodeError, UnicodeDecodeError):
            response.headers["X-Correlation-Id"] = corr_id
            return response
