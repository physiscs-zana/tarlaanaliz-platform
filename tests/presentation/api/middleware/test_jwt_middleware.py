# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-050: JWT middleware tests — token validation, phone_verified gate, bypass routes.

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.presentation.api.middleware.jwt_middleware import JwtMiddleware
from src.presentation.api.settings import settings


def _make_hs256_token(payload: dict[str, object]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    # Ensure exp and iat are always present (SEC-FIX: exp is required)
    if "exp" not in payload:
        payload["exp"] = int(time.time()) + 3600
    if "iat" not in payload:
        payload["iat"] = int(time.time())

    def _enc(data: dict[str, object]) -> str:
        encoded = base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode("utf-8"))
        return encoded.decode("utf-8").rstrip("=")

    header_b64 = _enc(header)
    payload_b64 = _enc(payload)
    msg = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = hmac.new(settings.jwt.secret.encode("utf-8"), msg, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(JwtMiddleware)

    @app.get("/private")
    def private(request: Request) -> dict[str, object]:
        user = request.state.user
        return {"subject": user.subject, "permissions": request.state.permissions}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"ok": "ok"}

    return app


def test_jwt_missing_bearer_returns_401() -> None:
    client = TestClient(_app())
    response = client.get("/private")
    assert response.status_code == 401
    assert "X-Correlation-Id" in response.headers


def test_jwt_invalid_signature_returns_401() -> None:
    client = TestClient(_app())
    token = _make_hs256_token({"sub": "u-1", "phone_verified": True, "user_id": "42"}) + "tampered"
    response = client.get("/private", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_jwt_phone_not_verified_returns_403() -> None:
    client = TestClient(_app())
    token = _make_hs256_token({"sub": "u-1", "phone_verified": False, "user_id": "42"})
    response = client.get("/private", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_jwt_valid_token_sets_user_context() -> None:
    client = TestClient(_app())
    token = _make_hs256_token(
        {
            "sub": "user-subject",
            "phone_verified": True,
            "user_id": "42",
            "permissions": ["analysis.read"],
        }
    )
    response = client.get("/private", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["subject"] == "user-subject"
    assert response.json()["permissions"] == ["analysis.read"]


def test_jwt_bypass_route_without_token() -> None:
    client = TestClient(_app())
    response = client.get("/health")
    assert response.status_code == 200
