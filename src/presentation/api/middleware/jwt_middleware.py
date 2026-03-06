# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: contract-first claim gate for authenticated identity.
"""JWT authentication middleware for phone+PIN verified identities."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.presentation.api.middleware._shared import METRICS_HOOK, ensure_request_context, is_bypassed_path
from src.presentation.api.settings import settings

LOGGER = logging.getLogger("api.middleware.jwt")


@dataclass(slots=True)
class AuthenticatedUser:
    subject: str
    user_id: str | None
    phone_verified: bool


class JwtValidationError(Exception):
    """Raised when JWT validation fails."""


class JwtMiddleware(BaseHTTPMiddleware):
    """Validate bearer token and attach identity context to request.state."""

    def __init__(self, app: Any, token_decoder: Callable[[str], dict[str, Any]] | None = None) -> None:
        super().__init__(app)
        self._token_decoder = token_decoder or self._decode_token

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        corr_id, _ = ensure_request_context(request)

        if not settings.jwt.enabled or is_bypassed_path(request.url.path, settings.jwt.bypass_routes):
            response: Response = await call_next(request)
            response.headers["X-Correlation-Id"] = corr_id
            return response

        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            METRICS_HOOK.increment("auth_unauthorized_total")
            return self._error_response(corr_id, 401, "Unauthorized")

        token = header[len("Bearer ") :].strip()
        try:
            claims = self._token_decoder(token)
        except JwtValidationError:
            METRICS_HOOK.increment("auth_unauthorized_total")
            return self._error_response(corr_id, 401, "Unauthorized")

        if not claims.get("phone_verified", False):
            # KR-081: contract-first claim gate for authenticated identity context.
            METRICS_HOOK.increment("auth_forbidden_total")
            return self._error_response(corr_id, 403, "Forbidden")

        subject = str(claims.get("sub") or claims.get("subject") or "")
        if not subject:
            METRICS_HOOK.increment("auth_unauthorized_total")
            return self._error_response(corr_id, 401, "Unauthorized")

        request.state.user = AuthenticatedUser(
            subject=subject,
            user_id=str(claims["user_id"]) if claims.get("user_id") is not None else None,
            phone_verified=True,
        )
        request.state.permissions = list(claims.get("permissions", []))
        request.state.roles = list(claims.get("roles", []))

        response = await call_next(request)
        response.headers["X-Correlation-Id"] = corr_id
        return response

    @staticmethod
    def _error_response(corr_id: str, status_code: int, detail: str) -> JSONResponse:
        response = JSONResponse(status_code=status_code, content={"detail": detail})
        response.headers["X-Correlation-Id"] = corr_id
        return response

    def _decode_token(self, token: str) -> dict[str, Any]:
        parts = token.split(".")
        if len(parts) != 3:
            raise JwtValidationError("Malformed token")

        header_raw, payload_raw, signature_raw = parts
        header = self._json_b64url_decode(header_raw)
        payload = self._json_b64url_decode(payload_raw)

        algorithm = str(header.get("alg", ""))
        expected_algorithm = settings.jwt.algorithm
        if algorithm != expected_algorithm:
            raise JwtValidationError("Algorithm mismatch")

        if expected_algorithm != "HS256":
            raise JwtValidationError("Unsupported algorithm")

        signed_content = f"{header_raw}.{payload_raw}".encode("utf-8")
        expected_signature = hmac.new(
            settings.jwt.secret.encode("utf-8"),
            signed_content,
            hashlib.sha256,
        ).digest()
        received_signature = self._b64url_decode(signature_raw)
        if not hmac.compare_digest(expected_signature, received_signature):
            LOGGER.info("JWT signature validation failed", extra={"event": "jwt_invalid_signature"})
            raise JwtValidationError("Invalid signature")

        # KR-050: Token expiration check (CRITICAL: was missing — expired tokens were accepted)
        now = int(time.time())
        exp = payload.get("exp")
        if exp is not None and now >= int(exp):
            LOGGER.info("JWT token expired", extra={"event": "jwt_expired"})
            raise JwtValidationError("Token expired")

        # iat sanity check — reject tokens issued in the future (clock skew > 60s)
        iat = payload.get("iat")
        if iat is not None and int(iat) > now + 60:
            raise JwtValidationError("Token issued in the future")

        return payload

    @staticmethod
    def _json_b64url_decode(data: str) -> dict[str, Any]:
        decoded = JwtMiddleware._b64url_decode(data)
        try:
            result: dict[str, Any] = json.loads(decoded.decode("utf-8"))
            return result
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise JwtValidationError("Invalid payload") from exc

    @staticmethod
    def _b64url_decode(data: str) -> bytes:
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(data + padding)
