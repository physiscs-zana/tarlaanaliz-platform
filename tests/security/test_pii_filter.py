# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# SC-SEC-05: PII sizma testi; IL_OPERATOR PII goremez.
"""PII filter security tests.

KR-066: PII ayri veri alaninda tutulur; CENTRAL_ADMIN disindaki roller PII goremez.
SC-SEC-05: Il Operatoru roluyle PII endpoint'ine erismeyi dene → veri donmez.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.presentation.api.middleware.pii_filter import PIIFilterMiddleware, _redact_dict


@dataclass
class FakeUser:
    roles: list[str]


def _pii_app() -> FastAPI:
    """Test icin PII iceren endpoint'li uygulama."""
    app = FastAPI()
    app.add_middleware(PIIFilterMiddleware)

    @app.get("/api/v1/users/{user_id}")
    def get_user(request: Request, user_id: str) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "full_name": "Ali Yilmaz",
            "phone": "05321234567",
            "iban": "TR330006100519786457841326",
            "field_count": 5,
            "district": "Harran",
        }

    return app


def test_pii_redacted_for_unauthenticated_user() -> None:
    """Dogrulanmamis kullanici icin PII maskelenmeli."""
    client = TestClient(_pii_app())
    resp = client.get("/api/v1/users/u123")

    assert resp.status_code == 200
    data = resp.json()
    # PII alanlari maskelenmis olmali
    assert data["full_name"] != "Ali Yilmaz"
    assert data["phone"] != "05321234567"
    assert data["iban"] != "TR330006100519786457841326"
    # PII olmayan alanlar korunmali
    assert data["field_count"] == 5
    assert data["district"] == "Harran"


def test_pii_redacted_for_il_operator() -> None:
    """KR-083/SC-SEC-05: IL_OPERATOR rolu PII goremez."""
    app = _pii_app()

    @app.middleware("http")
    async def set_role(request: Request, call_next: Any) -> Any:
        request.state.user = FakeUser(roles=["IL_OPERATOR"])
        request.state.roles = ["IL_OPERATOR"]
        return await call_next(request)

    client = TestClient(app)
    resp = client.get("/api/v1/users/u123")

    assert resp.status_code == 200
    data = resp.json()
    assert data["phone"] != "05321234567"
    assert data["full_name"] != "Ali Yilmaz"


def test_pii_visible_for_central_admin() -> None:
    """CENTRAL_ADMIN rolu PII gorebilir."""
    app = _pii_app()

    @app.middleware("http")
    async def set_role(request: Request, call_next: Any) -> Any:
        request.state.user = FakeUser(roles=["CENTRAL_ADMIN"])
        request.state.roles = ["CENTRAL_ADMIN"]
        return await call_next(request)

    client = TestClient(app)
    resp = client.get("/api/v1/users/u123")

    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Ali Yilmaz"
    assert data["phone"] == "05321234567"
    assert data["iban"] == "TR330006100519786457841326"


def test_redact_dict_masks_nested_pii() -> None:
    """Ic ice dict'lerdeki PII alanlari maskelenmeli."""
    data = {
        "mission_id": "m123",
        "farmer": {
            "phone": "05321234567",
            "full_name": "Ayse Demir",
        },
        "field_count": 3,
    }
    result = _redact_dict(data)

    assert result["mission_id"] == "m123"
    assert result["field_count"] == 3
    assert result["farmer"]["phone"] != "05321234567"
    assert result["farmer"]["full_name"] != "Ayse Demir"
    assert "***" in result["farmer"]["phone"] or len(result["farmer"]["phone"]) < 11


def test_redact_dict_masks_list_items() -> None:
    """Liste icerisindeki dict'lerin PII alanlari maskelenmeli."""
    data = {
        "users": [
            {"phone": "05551112233", "district": "Ceylanpinar"},
            {"phone": "05449876543", "district": "Akcakale"},
        ]
    }
    result = _redact_dict(data)

    for user in result["users"]:
        assert user["phone"] != "05551112233"
        assert user["phone"] != "05449876543"
        assert "district" in user  # PII olmayan alan korunmali
