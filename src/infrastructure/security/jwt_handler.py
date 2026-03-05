# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-050: JWT HS256 token üretimi ve doğrulaması (telefon+PIN kimlik).

"""Infrastructure JWT primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, cast

from jose import JWTError, jwt


@dataclass(frozen=True)
class JWTSettings:
    """Contract-first JWT configuration."""

    secret_key: str
    algorithm: str = "HS256"
    access_token_ttl_minutes: int = 30
    issuer: str = "tarlaanaliz-platform"
    audience: str = "tarlaanaliz-api"


class JWTHandler:
    """Small wrapper for token issue/verify."""

    def __init__(self, settings: JWTSettings) -> None:
        self._settings = settings

    def issue_access_token(self, subject: str, claims: dict[str, Any] | None = None) -> str:
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._settings.access_token_ttl_minutes)).timestamp()),
            "iss": self._settings.issuer,
            "aud": self._settings.audience,
        }
        if claims:
            payload.update(claims)
        return cast(str, jwt.encode(payload, self._settings.secret_key, algorithm=self._settings.algorithm))

    def verify_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self._settings.secret_key,
                algorithms=[self._settings.algorithm],
                audience=self._settings.audience,
                issuer=self._settings.issuer,
            )
        except JWTError as exc:
            raise ValueError("Invalid JWT token") from exc

        if not payload.get("sub"):
            raise ValueError("JWT token must include 'sub' claim")
        return cast(dict[str, Any], payload)
