# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-063: RBAC yetki matrisi; KR-017: Pilot sonuc raporunu GORMEZ.
"""RBAC negative boundary tests.

KR-063: Roller ve yetkiler (RBAC) — her rol yalnizca kendine tanimli
        kaynaklara erisebilir.
KR-017: Pilot tarafinda gorunen gorev bilgisi sadece MissionID, il/ilce,
        ada/parsel, bitki turu. Ciftci adi/telefonu gosterilmez.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


@dataclass
class FakeUser:
    user_id: str
    roles: list[str]


def _require_roles(*required_roles: str):
    """Basit rol kontrol dependency."""
    def _guard(request: Request) -> FakeUser:
        user = getattr(request.state, "user", None)
        if user is None:
            raise _forbidden("Dogrulama gerekli")
        user_roles = set(user.roles)
        if not user_roles & set(required_roles):
            raise _forbidden(f"Yetkisiz erisim. Gerekli roller: {required_roles}")
        return user
    return _guard


def _forbidden(detail: str) -> Exception:
    from fastapi import HTTPException
    return HTTPException(status_code=403, detail=detail)


def _rbac_app() -> FastAPI:
    """Test icin RBAC kontrollü uygulama."""
    app = FastAPI()

    @app.get("/api/v1/results/{mission_id}")
    def get_results(
        mission_id: str,
        _user: FakeUser = Depends(_require_roles("FARMER_SINGLE", "CENTRAL_ADMIN")),
    ) -> dict[str, Any]:
        return {
            "mission_id": mission_id,
            "health_score": 0.85,
            "layers": ["HEALTH", "WEED", "DISEASE"],
        }

    @app.get("/api/v1/admin/pricing")
    def get_pricing(
        _user: FakeUser = Depends(_require_roles("CENTRAL_ADMIN")),
    ) -> dict[str, Any]:
        return {"price_book_version": "2026-01"}

    @app.get("/api/v1/pilot/missions")
    def get_pilot_missions(
        _user: FakeUser = Depends(_require_roles("PILOT")),
    ) -> list[dict[str, Any]]:
        return [
            {"mission_id": "m001", "parcel_ref": "Harran/123/45", "crop_type": "PAMUK"},
        ]

    return app


def _client_with_role(app: FastAPI, user_id: str, roles: list[str]) -> TestClient:
    """Belirli rolle istek gonderen test client'i olusturur."""
    @app.middleware("http")
    async def inject_user(request: Request, call_next: Any) -> Any:
        request.state.user = FakeUser(user_id=user_id, roles=roles)
        return await call_next(request)
    return TestClient(app)


def test_pilot_cannot_access_results() -> None:
    """KR-017: Pilot sonuc raporunu GOREMEZ → 403."""
    app = _rbac_app()
    client = _client_with_role(app, "pilot_01", ["PILOT"])

    resp = client.get("/api/v1/results/m001")
    assert resp.status_code == 403


def test_farmer_can_access_results() -> None:
    """Ciftci kendi analiz sonuclarini gorebilir."""
    app = _rbac_app()
    client = _client_with_role(app, "farmer_01", ["FARMER_SINGLE"])

    resp = client.get("/api/v1/results/m001")
    assert resp.status_code == 200
    assert "health_score" in resp.json()


def test_pilot_cannot_access_admin_pricing() -> None:
    """Pilot admin fiyat endpoint'ine erisemez → 403."""
    app = _rbac_app()
    client = _client_with_role(app, "pilot_01", ["PILOT"])

    resp = client.get("/api/v1/admin/pricing")
    assert resp.status_code == 403


def test_farmer_cannot_access_admin_pricing() -> None:
    """Ciftci admin fiyat endpoint'ine erisemez → 403."""
    app = _rbac_app()
    client = _client_with_role(app, "farmer_01", ["FARMER_SINGLE"])

    resp = client.get("/api/v1/admin/pricing")
    assert resp.status_code == 403


def test_central_admin_can_access_pricing() -> None:
    """CENTRAL_ADMIN fiyat endpoint'ine erisebilir."""
    app = _rbac_app()
    client = _client_with_role(app, "admin_01", ["CENTRAL_ADMIN"])

    resp = client.get("/api/v1/admin/pricing")
    assert resp.status_code == 200


def test_pilot_can_access_own_missions() -> None:
    """Pilot kendi gorevlerini gorebilir."""
    app = _rbac_app()
    client = _client_with_role(app, "pilot_01", ["PILOT"])

    resp = client.get("/api/v1/pilot/missions")
    assert resp.status_code == 200
    missions = resp.json()
    assert len(missions) >= 1
    # PII olmamali; sadece MissionID/ParcelRef/CropType
    mission = missions[0]
    assert "mission_id" in mission
    assert "parcel_ref" in mission
    assert "farmer_name" not in mission
    assert "farmer_phone" not in mission
