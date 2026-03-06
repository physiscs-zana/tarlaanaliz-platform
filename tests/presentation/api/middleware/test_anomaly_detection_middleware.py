# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033: anomaly detection middleware test coverage.

from __future__ import annotations

import logging

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from src.presentation.api.middleware._shared import METRICS_HOOK
from src.presentation.api.middleware.anomaly_detection_middleware import AnomalyDetectionMiddleware
from src.presentation.api.settings import settings


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(AnomalyDetectionMiddleware)

    @app.get("/unstable")
    def unstable(response: Response, fail: bool = True) -> dict[str, str]:
        if fail:
            response.status_code = 500
        return {"ok": "ok"}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"ok": "ok"}

    return app


def test_anomaly_skips_allowlist_path() -> None:
    client = TestClient(_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Correlation-Id" in response.headers


def test_anomaly_detects_error_spike_and_logs(caplog, monkeypatch) -> None:
    monkeypatch.setattr(settings.anomaly, "rapid_repeat_window_seconds", 120)
    monkeypatch.setattr(settings.anomaly, "rapid_repeat_threshold", 4)
    caplog.set_level(logging.WARNING)
    client = TestClient(_app())

    for _ in range(4):
        client.get("/unstable", params={"fail": "true"})

    assert any("AnomalyDetected" in r.message for r in caplog.records)


def test_anomaly_detects_large_body(monkeypatch, caplog) -> None:
    monkeypatch.setattr(settings.anomaly, "large_body_threshold_bytes", 10)
    monkeypatch.setattr(settings.anomaly, "rapid_repeat_threshold", 1)
    caplog.set_level(logging.WARNING)
    client = TestClient(_app())
    response = client.get(
        "/unstable",
        params={"fail": "false"},
        headers={"content-length": "100", "user-agent": "suspicious-bot/1.0"},
    )
    assert response.status_code == 200
    assert any("AnomalyDetected" in r.message for r in caplog.records)


def test_anomaly_metrics_status_counter_changes() -> None:
    before = METRICS_HOOK.counters.get("http_status_total:500", 0)
    client = TestClient(_app())
    _ = client.get("/unstable", params={"fail": "true"})
    after = METRICS_HOOK.counters.get("http_status_total:500", 0)
    assert after >= before + 1
