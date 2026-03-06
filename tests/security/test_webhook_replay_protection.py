# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033: Odeme webhook replay korumasi.
"""Webhook replay protection security tests.

KR-033: Odeme saglayici webhook callback'lerinde replay saldirisi onleme.
Ayni idempotency_key ile tekrar gelen istekler reddedilmeli (duplicate).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


def _webhook_app() -> FastAPI:
    """Test icin webhook replay korumali uygulama."""
    app = FastAPI()

    _processed_keys: set[str] = set()

    @app.post("/api/v1/payments/webhook/provider")
    async def payment_webhook(request: Request) -> JSONResponse:
        body = await request.json()
        idempotency_key = body.get("idempotency_key")

        if not idempotency_key:
            return JSONResponse(
                status_code=400,
                content={"detail": "idempotency_key gerekli"},
            )

        if idempotency_key in _processed_keys:
            return JSONResponse(
                status_code=409,
                content={
                    "detail": "Duplicate webhook — zaten islendi",
                    "idempotency_key": idempotency_key,
                },
            )

        _processed_keys.add(idempotency_key)
        return JSONResponse(
            status_code=200,
            content={"status": "processed", "idempotency_key": idempotency_key},
        )

    return app


def test_webhook_first_request_succeeds() -> None:
    """Ilk webhook istegi basarili olmali."""
    client = TestClient(_webhook_app())
    resp = client.post(
        "/api/v1/payments/webhook/provider",
        json={"idempotency_key": "wh_001", "event": "payment.completed"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "processed"


def test_webhook_replay_returns_409() -> None:
    """Ayni idempotency_key ile tekrar gelen istek 409 donmeli."""
    client = TestClient(_webhook_app())
    payload: dict[str, Any] = {
        "idempotency_key": "wh_002",
        "event": "payment.completed",
    }

    first = client.post("/api/v1/payments/webhook/provider", json=payload)
    assert first.status_code == 200

    replay = client.post("/api/v1/payments/webhook/provider", json=payload)
    assert replay.status_code == 409
    assert "Duplicate" in replay.json()["detail"]


def test_webhook_different_keys_both_succeed() -> None:
    """Farkli idempotency_key'ler ile istekler basarili olmali."""
    client = TestClient(_webhook_app())

    resp1 = client.post(
        "/api/v1/payments/webhook/provider",
        json={"idempotency_key": "wh_003", "event": "payment.completed"},
    )
    resp2 = client.post(
        "/api/v1/payments/webhook/provider",
        json={"idempotency_key": "wh_004", "event": "payment.completed"},
    )

    assert resp1.status_code == 200
    assert resp2.status_code == 200


def test_webhook_missing_idempotency_key_returns_400() -> None:
    """idempotency_key olmadan gelen istek 400 donmeli."""
    client = TestClient(_webhook_app())
    resp = client.post(
        "/api/v1/payments/webhook/provider",
        json={"event": "payment.completed"},
    )
    assert resp.status_code == 400
    assert "idempotency_key" in resp.json()["detail"]
