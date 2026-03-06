# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-071: mTLS cihaz kimlik dogrulamasi.
"""mTLS verification security tests.

KR-071: EdgeKiosk → Platform/Ingress: HTTPS 443 uzerinden, mTLS cihaz kimligi ile.
SC-SEC-03: Sertifikasiz/yanlis sertifikali istek → deny + audit.

Bu testler, mTLS middleware'inin ingest endpoint'lerinde sertifika
dogrulamasini zorunlu kıldigini dogrular.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.presentation.api.middleware.mtls_verifier import MTLSVerifierMiddleware


def _mtls_app(registered_fingerprints: frozenset[str] | None = None) -> FastAPI:
    """Test icin mTLS korumali uygulama."""
    app = FastAPI()
    app.add_middleware(
        MTLSVerifierMiddleware,
        registered_fingerprints=registered_fingerprints,
    )

    @app.post("/api/v1/ingest/upload")
    def upload() -> dict[str, str]:
        return {"status": "uploaded"}

    @app.get("/api/v1/fields")
    def list_fields() -> dict[str, str]:
        return {"ok": "ok"}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"ok": "ok"}

    return app


def test_ingest_without_cert_returns_403() -> None:
    """Sertifikasiz ingest istegi 403 donmeli (KR-071)."""
    client = TestClient(_mtls_app())

    resp = client.post("/api/v1/ingest/upload")

    assert resp.status_code == 403
    data = resp.json()
    assert "mTLS" in data["detail"] or "sertifika" in data["detail"]
    assert "corr_id" in data


def test_ingest_with_cert_succeeds() -> None:
    """Gecerli sertifika ile ingest istegi basarili olmali."""
    client = TestClient(_mtls_app())

    resp = client.post(
        "/api/v1/ingest/upload",
        headers={
            "X-SSL-Client-Cert": "-----BEGIN CERTIFICATE-----\nMIIBtest\n-----END CERTIFICATE-----",
            "X-SSL-Client-Verify": "SUCCESS",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "uploaded"


def test_ingest_with_failed_verify_returns_403() -> None:
    """Dogrulama basarisiz sertifika ile 403 donmeli."""
    client = TestClient(_mtls_app())

    resp = client.post(
        "/api/v1/ingest/upload",
        headers={
            "X-SSL-Client-Cert": "-----BEGIN CERTIFICATE-----\nMIIBtest\n-----END CERTIFICATE-----",
            "X-SSL-Client-Verify": "FAILED",
        },
    )

    assert resp.status_code == 403
    assert "corr_id" in resp.json()


def test_non_ingest_endpoint_bypasses_mtls() -> None:
    """Ingest olmayan endpoint'ler mTLS'den muaf olmali."""
    client = TestClient(_mtls_app())

    resp = client.get("/api/v1/fields")

    assert resp.status_code == 200


def test_health_bypasses_mtls() -> None:
    """Health endpoint mTLS'den muaf olmali."""
    client = TestClient(_mtls_app())

    resp = client.get("/health")

    assert resp.status_code == 200


def test_unregistered_fingerprint_returns_403() -> None:
    """Kayitsiz sertifika parmak izi ile 403 donmeli."""
    # Bos fingerprint seti = sadece kayitli sertifikalar kabul edilir
    client = TestClient(_mtls_app(registered_fingerprints=frozenset({"abc123"})))

    resp = client.post(
        "/api/v1/ingest/upload",
        headers={
            "X-SSL-Client-Cert": "-----BEGIN CERTIFICATE-----\nMIIBtest\n-----END CERTIFICATE-----",
            "X-SSL-Client-Verify": "SUCCESS",
        },
    )

    assert resp.status_code == 403
    assert "Kayitsiz" in resp.json()["detail"] or "corr_id" in resp.json()


def test_403_response_includes_correlation_id() -> None:
    """mTLS red response'unda X-Correlation-Id olmali."""
    client = TestClient(_mtls_app())

    resp = client.post("/api/v1/ingest/upload")

    assert resp.status_code == 403
    assert "X-Correlation-Id" in resp.headers
