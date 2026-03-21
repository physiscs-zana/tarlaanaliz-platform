# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Test modülü; davranış doğrulama ve regresyon engeli.
Sorumluluk: Bağlamına göre beklenen sorumlulukları yerine getirir; SSOT v1.0.0 ile uyumlu kalır.
Girdi/Çıktı (Contract/DTO/Event): N/A
Güvenlik (RBAC/PII/Audit): N/A
Hata Modları (idempotency/retry/rate limit): N/A
Observability (log fields/metrics/traces): N/A
Testler: N/A
Bağımlılıklar: N/A
Notlar/SSOT: Tek referans: SSOT v1.0.0. Aynı kavram başka yerde tekrar edilmez.
"""

from __future__ import annotations

import pytest

shapely = pytest.importorskip("shapely", reason="shapely not installed — PostGIS tests skipped")

from src.core.domain.value_objects.geometry import Geometry, GeometryError


def test_geometry_from_geojson_polygon_and_to_geojson() -> None:
    geojson = {
        "type": "Polygon",
        "coordinates": [[[32.0, 37.0], [32.1, 37.0], [32.1, 37.1], [32.0, 37.1], [32.0, 37.0]]],
    }

    geom = Geometry.from_geojson(geojson)

    assert geom.geom_type == "Polygon"
    assert geom.to_geojson()["type"] == "Polygon"


def test_geometry_rejects_invalid_payload() -> None:
    with pytest.raises(GeometryError, match="type"):
        Geometry.from_geojson({"coordinates": []})
