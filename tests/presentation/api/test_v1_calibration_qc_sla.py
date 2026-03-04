# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: SDLC gate tests for calibration, QC, and SLA endpoints.
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.presentation.api.dependencies import (
    CalibrationRecordCreateRequest,
    CalibrationRecordResponse,
    QCReportCreateRequest,
    QCReportResponse,
    QCStatus,
    SLABreachResponse,
    SLASummaryResponse,
)
from src.presentation.api.v1.endpoints.calibration import router as calibration_router
from src.presentation.api.v1.endpoints.qc import router as qc_router
from src.presentation.api.v1.endpoints.sla_metrics import router as sla_router


class StubCalibrationService:
    def create_record(self, *, actor_user_id: str, payload: CalibrationRecordCreateRequest, corr_id: str | None) -> CalibrationRecordResponse:
        return CalibrationRecordResponse(record_id=uuid4(), created_at=datetime.now(timezone.utc), **payload.model_dump())

    def get_record(self, *, record_id, corr_id):
        return None

    def list_records(self, *, corr_id, drone_id, field_id, start_at, end_at):
        return []


class StubQCService:
    def create_report(self, *, actor_user_id: str, payload: QCReportCreateRequest, corr_id: str | None) -> QCReportResponse:
        return QCReportResponse(report_id=uuid4(), created_at=datetime.now(timezone.utc), **payload.model_dump())

    def get_report(self, *, report_id, corr_id):
        return None

    def list_reports(self, *, corr_id, calibration_record_id, status_filter, start_at, end_at):
        return []


class StubSLAService:
    def get_summary(self, *, start_at, end_at, corr_id):
        return SLASummaryResponse(
            window_start=datetime.now(timezone.utc),
            window_end=datetime.now(timezone.utc),
            p95_latency_ms=25.0,
            error_rate=0.01,
            backlog=1,
        )

    def list_breaches(self, *, start_at, end_at, corr_id):
        return [
            SLABreachResponse(
                breach_id=uuid4(),
                metric_name="p95_latency",
                threshold=100,
                observed_value=120,
                started_at=datetime.now(timezone.utc),
                resolved_at=None,
            )
        ]


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(calibration_router)
    app.include_router(qc_router)
    app.include_router(sla_router)
    app.state.calibration_service = StubCalibrationService()
    app.state.qc_service = StubQCService()
    app.state.sla_metrics_service = StubSLAService()

    @app.middleware("http")
    async def add_state(request: Request, call_next):
        request.state.user = {"user_id": "u-1", "roles": ["farmer"], "permissions": []}
        request.state.corr_id = "corr-2"
        return await call_next(request)

    return app


def test_qc_create_accepts_status_enum_and_sets_header() -> None:
    client = TestClient(_build_app())
    response = client.post(
        "/qc/reports",
        json={"calibration_record_id": str(uuid4()), "status": QCStatus.PASS, "checks": {"n": 1}, "evidence_refs": ["s3://ref"]},
    )

    assert response.status_code == 201
    assert response.headers["X-Correlation-Id"] == "corr-2"


def test_sla_summary_readonly_endpoint() -> None:
    client = TestClient(_build_app())
    response = client.get("/sla/summary")

    assert response.status_code == 200
    assert "p95_latency_ms" in response.json()
