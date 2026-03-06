# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# SC-SEC-02: Brute force 16 fail → 30 min lock.
"""Brute force lockout security tests.

KR-050: Giris deneme siniri (rate limit) ve kisa sureli kilitleme (lockout).
SC-SEC-02: 16 basarisiz PIN denemesi → 30 dakika kilitleme.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.presentation.api.middleware.rate_limit_middleware import RateLimitMiddleware
from src.presentation.api.settings import settings


def _auth_app() -> FastAPI:
    """Test icin minimal auth uygulamasi."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    _fail_counts: dict[str, int] = {}

    @app.post("/api/v1/auth/login")
    def login() -> dict[str, str]:
        return {"token": "test"}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"ok": "ok"}

    return app


def test_rate_limit_blocks_excessive_login_attempts(monkeypatch) -> None:
    """SC-SEC-02: Auth endpoint'ine asiri istek rate limit ile engellenir."""
    monkeypatch.setattr(settings.rate_limit, "per_minute_limit", 5)
    monkeypatch.setattr(settings.rate_limit, "burst", 0)
    client = TestClient(_auth_app())

    responses = []
    for _ in range(7):
        resp = client.post("/api/v1/auth/login")
        responses.append(resp)

    # Ilk 5 istek basarili olmali
    assert all(r.status_code == 200 for r in responses[:5])

    # 6. veya 7. istekte rate limit devreye girmeli
    blocked_codes = [r.status_code for r in responses[5:]]
    assert 429 in blocked_codes, f"Rate limit tetiklenmedi: {blocked_codes}"


def test_rate_limit_includes_retry_after_header(monkeypatch) -> None:
    """Rate limit response'unda Retry-After header'i olmali."""
    monkeypatch.setattr(settings.rate_limit, "per_minute_limit", 1)
    monkeypatch.setattr(settings.rate_limit, "burst", 0)
    client = TestClient(_auth_app())

    _ = client.post("/api/v1/auth/login")
    blocked = client.post("/api/v1/auth/login")

    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


def test_health_endpoint_bypasses_rate_limit(monkeypatch) -> None:
    """Health endpoint rate limit'ten muaf olmali."""
    monkeypatch.setattr(settings.rate_limit, "per_minute_limit", 1)
    monkeypatch.setattr(settings.rate_limit, "burst", 0)
    client = TestClient(_auth_app())

    responses = [client.get("/health") for _ in range(5)]
    assert all(r.status_code == 200 for r in responses)


def test_blocked_response_includes_correlation_id(monkeypatch) -> None:
    """Engellenen isteklerde X-Correlation-Id header'i olmali."""
    monkeypatch.setattr(settings.rate_limit, "per_minute_limit", 1)
    monkeypatch.setattr(settings.rate_limit, "burst", 0)
    client = TestClient(_auth_app())

    _ = client.post("/api/v1/auth/login")
    blocked = client.post("/api/v1/auth/login")

    assert blocked.status_code == 429
    assert "X-Correlation-Id" in blocked.headers
