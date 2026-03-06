# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-083: Il operatoru koordinat anonimizasyonu.
"""Grid anonymization security tests.

KR-083: Il Operatoru PII GOREMEZ; sunumu iki katmanli:
  (A) Merkez — PII ayri
  (B) Operatoru — SubscriberRef + ilce veya 1-2 km grid

Bu testler, grid anonymizer middleware'inin koordinatlari dogru sekilde
anonimize ettigini ve PII alanlarini kaldirigini dogrular.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.presentation.api.middleware.grid_anonymizer import (
    GridAnonymizerMiddleware,
    _anonymize_dict,
    _pseudonymize_field_id,
    _snap_to_grid,
)


@dataclass
class FakeUser:
    roles: list[str]


def _geo_app() -> FastAPI:
    """Test icin koordinat iceren endpoint'li uygulama."""
    app = FastAPI()
    app.add_middleware(GridAnonymizerMiddleware)

    @app.get("/api/v1/kpi/field-density")
    def field_density(request: Request) -> dict[str, Any]:
        return {
            "district": "Harran",
            "field_id": "FLD-12345-ABCDE",
            "latitude": 36.86543,
            "longitude": 39.02178,
            "farmer_name": "Ali Yilmaz",
            "farmer_phone": "05321234567",
            "field_count": 42,
            "total_donum": 15000,
        }

    return app


def _client_with_role(app: FastAPI, roles: list[str]) -> TestClient:
    """Belirli rolle test client olusturur."""

    @app.middleware("http")
    async def inject_user(request: Request, call_next: Any) -> Any:
        request.state.user = FakeUser(roles=roles)
        return await call_next(request)

    return TestClient(app)


def test_il_operator_gets_anonymized_coordinates() -> None:
    """KR-083: IL_OPERATOR icin koordinatlar grid'e yuvarlanmali."""
    app = _geo_app()
    client = _client_with_role(app, ["IL_OPERATOR"])

    resp = client.get("/api/v1/kpi/field-density")
    data = resp.json()

    assert resp.status_code == 200
    # Koordinatlar tam deger olmamali
    assert data["latitude"] != 36.86543
    assert data["longitude"] != 39.02178


def test_il_operator_field_id_pseudonymized() -> None:
    """KR-083: IL_OPERATOR icin FieldID pseudonymous olmali."""
    app = _geo_app()
    client = _client_with_role(app, ["IL_OPERATOR"])

    resp = client.get("/api/v1/kpi/field-density")
    data = resp.json()

    assert data["field_id"] != "FLD-12345-ABCDE"
    assert data["field_id"].startswith("FR-")


def test_il_operator_pii_stripped() -> None:
    """KR-083: IL_OPERATOR icin ciftci adi/telefonu kaldirilmali."""
    app = _geo_app()
    client = _client_with_role(app, ["IL_OPERATOR"])

    resp = client.get("/api/v1/kpi/field-density")
    data = resp.json()

    assert "farmer_name" not in data
    assert "farmer_phone" not in data


def test_il_operator_kpi_data_preserved() -> None:
    """KR-083: IL_OPERATOR icin aggregate KPI korunmali."""
    app = _geo_app()
    client = _client_with_role(app, ["IL_OPERATOR"])

    resp = client.get("/api/v1/kpi/field-density")
    data = resp.json()

    assert data["district"] == "Harran"
    assert data["field_count"] == 42
    assert data["total_donum"] == 15000


def test_admin_gets_full_data() -> None:
    """CENTRAL_ADMIN tum verileri gorebilir (anonimizasyon yok)."""
    app = _geo_app()
    client = _client_with_role(app, ["CENTRAL_ADMIN"])

    resp = client.get("/api/v1/kpi/field-density")
    data = resp.json()

    assert data["latitude"] == 36.86543
    assert data["longitude"] == 39.02178
    assert data["field_id"] == "FLD-12345-ABCDE"
    assert data["farmer_name"] == "Ali Yilmaz"


def test_snap_to_grid_reduces_precision() -> None:
    """Grid snap fonksiyonu koordinat hassasiyetini azaltmali."""
    original = 36.86543
    snapped = _snap_to_grid(original)

    # Snap sonrasi deger orijinalden farkli olmali
    assert snapped != original
    # Grid boyutu ~0.015 derece; fark en fazla 0.015
    assert abs(snapped - original) < 0.015


def test_pseudonymize_field_id_deterministic() -> None:
    """Ayni FieldID her seferinde ayni ref uretmeli."""
    ref1 = _pseudonymize_field_id("FLD-12345-ABCDE")
    ref2 = _pseudonymize_field_id("FLD-12345-ABCDE")

    assert ref1 == ref2
    assert ref1.startswith("FR-")


def test_pseudonymize_different_ids_produce_different_refs() -> None:
    """Farkli FieldID'ler farkli ref uretmeli."""
    ref1 = _pseudonymize_field_id("FLD-12345-ABCDE")
    ref2 = _pseudonymize_field_id("FLD-67890-FGHIJ")

    assert ref1 != ref2


def test_anonymize_dict_handles_nested_data() -> None:
    """Ic ice dict'lerdeki koordinatlar anonimize edilmeli."""
    data = {
        "fields": [
            {
                "field_id": "FLD-001",
                "latitude": 37.5,
                "longitude": 38.5,
                "farmer_name": "Test",
            }
        ]
    }
    result = _anonymize_dict(data)

    field = result["fields"][0]
    assert field["field_id"].startswith("FR-")
    assert field["latitude"] != 37.5
    assert "farmer_name" not in field
