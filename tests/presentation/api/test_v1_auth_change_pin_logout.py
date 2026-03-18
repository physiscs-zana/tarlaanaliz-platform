# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-050: PIN degistirme ve logout endpoint testleri.
# Contract: platform_public.v1.yaml — POST /auth/change-pin (200), POST /auth/logout (204).
"""Tests for change-pin and logout endpoints.

Each new endpoint has at least 1 happy-path + 1 error-case test
as required by project quality standards.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.presentation.api.main import create_app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def _make_jwt(secret: str = "test-only-insecure-key-do-not-use-in-prod", **extra_claims: object) -> str:
    """Create a minimal valid JWT for testing."""
    import base64
    import hashlib
    import hmac
    import json

    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    now = int(time.time())
    payload_dict = {
        "sub": "test-user-id-000",
        "iat": now,
        "exp": now + 1800,
        "phone": "+905551234567",
        "phone_verified": True,
        "roles": ["FARMER_SINGLE"],
        "user_id": "00000000-0000-0000-0000-000000000001",
        **extra_claims,
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).rstrip(b"=").decode()
    signature = (
        base64.urlsafe_b64encode(hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
        .rstrip(b"=")
        .decode()
    )
    return f"{header}.{payload}.{signature}"


# ============================================================
# POST /auth/logout — Contract: 204 No Content
# ============================================================


class TestLogout:
    """POST /api/v1/auth/logout tests."""

    def test_logout_happy_path_returns_204(self, client: TestClient) -> None:
        """Happy path: valid token → 204 No Content, no body."""
        token = _make_jwt()
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204
        assert response.content == b""  # No Content means empty body

    def test_logout_without_token_returns_204(self, client: TestClient) -> None:
        """Edge case: no Authorization header → still 204 (graceful)."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 204

    def test_logout_with_invalid_token_returns_204(self, client: TestClient) -> None:
        """Error case: malformed token → still 204 (best-effort blacklist)."""
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 204


# ============================================================
# POST /auth/phone-pin/change-pin — Contract: 200 Success
# ============================================================


class TestChangePin:
    """POST /api/v1/auth/phone-pin/change-pin tests."""

    def test_change_pin_without_auth_returns_401(self, client: TestClient) -> None:
        """Error case: no Authorization header → 401."""
        response = client.post(
            "/api/v1/auth/phone-pin/change-pin",
            json={"current_pin": "123456", "new_pin": "654321"},
        )
        assert response.status_code == 401

    def test_change_pin_invalid_pin_format_returns_422(self, client: TestClient) -> None:
        """Error case: non-numeric PIN → 422 validation error."""
        token = _make_jwt()
        response = client.post(
            "/api/v1/auth/phone-pin/change-pin",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_pin": "abcdef", "new_pin": "654321"},
        )
        assert response.status_code == 422

    def test_change_pin_short_pin_returns_422(self, client: TestClient) -> None:
        """Error case: PIN shorter than 6 digits → 422."""
        token = _make_jwt()
        response = client.post(
            "/api/v1/auth/phone-pin/change-pin",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_pin": "123", "new_pin": "654321"},
        )
        assert response.status_code == 422

    def test_change_pin_same_pin_returns_400(self, client: TestClient) -> None:
        """Error case: new PIN same as current → 400.

        Mocks the DB session to simulate a real user with known PIN hash.
        """
        token = _make_jwt()
        import bcrypt

        fake_hash = bcrypt.hashpw(b"123456", bcrypt.gensalt()).decode()
        fake_user = MagicMock()
        fake_user.pin_hash = fake_hash

        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = fake_user

        mock_session = AsyncMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_session
        mock_ctx.__aexit__.return_value = False

        with (
            patch(
                "src.infrastructure.persistence.sqlalchemy.session.get_async_session",
                return_value=mock_ctx,
            ),
            patch(
                "src.infrastructure.persistence.sqlalchemy.repositories.user_repository_impl.UserRepositoryImpl",
                return_value=mock_repo,
            ),
        ):
            response = client.post(
                "/api/v1/auth/phone-pin/change-pin",
                headers={"Authorization": f"Bearer {token}"},
                json={"current_pin": "123456", "new_pin": "123456"},
            )
        assert response.status_code == 400

    def test_change_pin_happy_path_returns_200(self, client: TestClient) -> None:
        """Happy path: valid current PIN + different new PIN → 200 Success.

        Mocks the DB session to simulate a real user with known PIN hash.
        Contract: {success: true, message: "..."} per responses.yaml#Success.
        """
        token = _make_jwt()
        import bcrypt

        fake_hash = bcrypt.hashpw(b"111111", bcrypt.gensalt()).decode()
        fake_user = MagicMock()
        fake_user.pin_hash = fake_hash
        fake_user.change_pin = MagicMock()

        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = fake_user

        mock_session = AsyncMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_session
        mock_ctx.__aexit__.return_value = False

        with (
            patch(
                "src.infrastructure.persistence.sqlalchemy.session.get_async_session",
                return_value=mock_ctx,
            ),
            patch(
                "src.infrastructure.persistence.sqlalchemy.repositories.user_repository_impl.UserRepositoryImpl",
                return_value=mock_repo,
            ),
        ):
            response = client.post(
                "/api/v1/auth/phone-pin/change-pin",
                headers={"Authorization": f"Bearer {token}"},
                json={"current_pin": "111111", "new_pin": "222222"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "message" in body
