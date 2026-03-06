# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# SC-SEC-01: Rate limit 61 req/min → HTTP 429.
"""Rate limit enforcement security tests.

KR-050: Giris deneme siniri ve kisa sureli kilitleme.
SC-SEC-01: 61 istek/dakika → HTTP 429.

Bu testler, rate limiting middleware'inin calistigindan emin olur.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.presentation.api.middleware.rate_limit_middleware import RateLimitMiddleware
from src.presentation.api.settings import settings


def _rate_app() -> FastAPI:
    """Test icin rate-limited uygulama."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/api/v1/fields")
    def list_fields() -> dict[str, str]:
        return {"ok": "ok"}

    @app.post("/api/v1/auth/login")
    def login() -> dict[str, str]:
        return {"token": "test"}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"ok": "ok"}

    return app


def test_requests_within_limit_succeed(monkeypatch) -> None:
    """Limit altindaki istekler basarili olmali."""
    monkeypatch.setattr(settings.rate_limit, "per_minute_limit", 10)
    monkeypatch.setattr(settings.rate_limit, "burst", 0)
    client = TestClient(_rate_app())

    responses = [client.get("/api/v1/fields") for _ in range(10)]
    assert all(r.status_code == 200 for r in responses)


def test_exceeding_limit_returns_429(monkeypatch) -> None:
    """SC-SEC-01: Limit asiminda 429 donmeli."""
    monkeypatch.setattr(settings.rate_limit, "per_minute_limit", 3)
    monkeypatch.setattr(settings.rate_limit, "burst", 0)
    client = TestClient(_rate_app())

    responses = [client.get("/api/v1/fields") for _ in range(5)]
    status_codes = [r.status_code for r in responses]

    assert 429 in status_codes, f"429 bekleniyor, alinan: {status_codes}"


def test_429_response_has_retry_after(monkeypatch) -> None:
    """429 response'unda Retry-After header'i olmali."""
    monkeypatch.setattr(settings.rate_limit, "per_minute_limit", 1)
    monkeypatch.setattr(settings.rate_limit, "burst", 0)
    client = TestClient(_rate_app())

    _ = client.get("/api/v1/fields")
    blocked = client.get("/api/v1/fields")

    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    retry_after = int(blocked.headers["Retry-After"])
    assert retry_after > 0


def test_429_response_has_correlation_id(monkeypatch) -> None:
    """429 response'unda X-Correlation-Id olmali."""
    monkeypatch.setattr(settings.rate_limit, "per_minute_limit", 1)
    monkeypatch.setattr(settings.rate_limit, "burst", 0)
    client = TestClient(_rate_app())

    _ = client.get("/api/v1/fields")
    blocked = client.get("/api/v1/fields")

    assert blocked.status_code == 429
    assert "X-Correlation-Id" in blocked.headers
    assert len(blocked.headers["X-Correlation-Id"]) > 0


def test_health_endpoint_not_rate_limited(monkeypatch) -> None:
    """Health endpoint rate limit'ten muaf."""
    monkeypatch.setattr(settings.rate_limit, "per_minute_limit", 1)
    monkeypatch.setattr(settings.rate_limit, "burst", 0)
    client = TestClient(_rate_app())

    responses = [client.get("/health") for _ in range(10)]
    assert all(r.status_code == 200 for r in responses)
