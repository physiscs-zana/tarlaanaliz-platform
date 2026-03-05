# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""QC report registration and query endpoints."""

from __future__ import annotations

import time
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from src.presentation.api.dependencies import (
    CurrentUser,
    MetricsCollector,
    QCReportCreateRequest,
    QCReportResponse,
    QCService,
    QCStatus,
    get_current_user,
    get_metrics_collector,
    get_qc_service,
)

router = APIRouter(
    prefix="/qc",
    tags=["qc"],
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}, 409: {"description": "Conflict"}, 422: {"description": "Validation error"}, 429: {"description": "Too many requests"}},
)


def _observe(request: Request, metrics: MetricsCollector, started: float, status_code: int) -> None:
    corr_id = getattr(request.state, "corr_id", None)
    route = request.url.path
    metrics.observe_http(route=route, method=request.method, status_code=status_code, latency_ms=(time.perf_counter() - started) * 1000, corr_id=corr_id)
    metrics.observe_status(route=route, status_code=status_code, corr_id=corr_id)


@router.post("/reports", response_model=QCReportResponse, status_code=status.HTTP_201_CREATED)
def create_qc_report(
    payload: QCReportCreateRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    service: QCService = Depends(get_qc_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> QCReportResponse:
    # KR-018: report registration endpoint, no analysis start.
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        report = service.create_report(actor_user_id=user.user_id, payload=payload, corr_id=corr_id)
        _observe(request, metrics, started, status.HTTP_201_CREATED)
        return report
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:  # noqa: BLE001
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.get("/reports/{report_id}", response_model=QCReportResponse)
def get_qc_report(
    report_id: UUID,
    request: Request,
    response: Response,
    _user: CurrentUser = Depends(get_current_user),
    service: QCService = Depends(get_qc_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> QCReportResponse:
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        report = service.get_report(report_id=report_id, corr_id=corr_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QC report not found")
        _observe(request, metrics, started, status.HTTP_200_OK)
        return report
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:  # noqa: BLE001
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.get("/reports", response_model=list[QCReportResponse])
def list_qc_reports(
    request: Request,
    response: Response,
    calibration_record_id: UUID | None = Query(default=None),
    status_filter: QCStatus | None = Query(default=None, alias="status"),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    _user: CurrentUser = Depends(get_current_user),
    service: QCService = Depends(get_qc_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> list[QCReportResponse]:
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        reports = service.list_reports(
            corr_id=corr_id,
            calibration_record_id=calibration_record_id,
            status_filter=status_filter,
            start_at=start_at,
            end_at=end_at,
        )
        _observe(request, metrics, started, status.HTTP_200_OK)
        return reports
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:  # noqa: BLE001
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


__all__ = ["router", "QCStatus"]
