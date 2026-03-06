# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Calibration record registration and query endpoints."""

from __future__ import annotations

import time
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from src.presentation.api.dependencies import (
    CalibrationRecordCreateRequest,
    CalibrationRecordResponse,
    CalibrationService,
    CurrentUser,
    MetricsCollector,
    get_calibration_service,
    get_current_user,
    get_metrics_collector,
)

router = APIRouter(
    prefix="/calibration",
    tags=["calibration"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        409: {"description": "Conflict"},
        422: {"description": "Validation error"},
        429: {"description": "Too many requests"},
    },
)


def _observe(request: Request, metrics: MetricsCollector, started: float, status_code: int) -> None:
    corr_id = getattr(request.state, "corr_id", None)
    route = request.url.path
    metrics.observe_http(
        route=route,
        method=request.method,
        status_code=status_code,
        latency_ms=(time.perf_counter() - started) * 1000,
        corr_id=corr_id,
    )
    metrics.observe_status(route=route, status_code=status_code, corr_id=corr_id)


@router.post("/records", response_model=CalibrationRecordResponse, status_code=status.HTTP_201_CREATED)
def create_calibration_record(
    payload: CalibrationRecordCreateRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    service: CalibrationService = Depends(get_calibration_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> CalibrationRecordResponse:
    # KR-018: this endpoint records calibration evidence only.
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        record = service.create_record(actor_user_id=user.user_id, payload=payload, corr_id=corr_id)
        _observe(request, metrics, started, status.HTTP_201_CREATED)
        return record
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:  # noqa: BLE001
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.get("/records/{record_id}", response_model=CalibrationRecordResponse)
def get_calibration_record(
    record_id: UUID,
    request: Request,
    response: Response,
    _user: CurrentUser = Depends(get_current_user),
    service: CalibrationService = Depends(get_calibration_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> CalibrationRecordResponse:
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        record = service.get_record(record_id=record_id, corr_id=corr_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calibration record not found")
        _observe(request, metrics, started, status.HTTP_200_OK)
        return record
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:  # noqa: BLE001
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.get("/records", response_model=list[CalibrationRecordResponse])
def list_calibration_records(
    request: Request,
    response: Response,
    drone_id: str | None = Query(default=None),
    field_id: UUID | None = Query(default=None),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    _user: CurrentUser = Depends(get_current_user),
    service: CalibrationService = Depends(get_calibration_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> list[CalibrationRecordResponse]:
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        records = service.list_records(
            corr_id=corr_id, drone_id=drone_id, field_id=field_id, start_at=start_at, end_at=end_at
        )
        _observe(request, metrics, started, status.HTTP_200_OK)
        return records
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:  # noqa: BLE001
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


__all__ = ["router"]
