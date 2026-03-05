# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Read-only SLA metrics endpoints."""

from __future__ import annotations

import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from src.presentation.api.dependencies import (
    CurrentUser,
    MetricsCollector,
    SLABreachResponse,
    SLAMetricsService,
    SLASummaryResponse,
    get_current_user,
    get_metrics_collector,
    get_sla_metrics_service,
)

router = APIRouter(
    prefix="/sla",
    tags=["sla"],
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}, 409: {"description": "Conflict"}, 422: {"description": "Validation error"}, 429: {"description": "Too many requests"}},
)


def _observe(request: Request, metrics: MetricsCollector, started: float, status_code: int) -> None:
    corr_id = getattr(request.state, "corr_id", None)
    route = request.url.path
    metrics.observe_http(route=route, method=request.method, status_code=status_code, latency_ms=(time.perf_counter() - started) * 1000, corr_id=corr_id)
    metrics.observe_status(route=route, status_code=status_code, corr_id=corr_id)


@router.get("/summary", response_model=SLASummaryResponse)
def get_sla_summary(
    request: Request,
    response: Response,
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    _user: CurrentUser = Depends(get_current_user),
    service: SLAMetricsService = Depends(get_sla_metrics_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> SLASummaryResponse:
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        summary = service.get_summary(start_at=start_at, end_at=end_at, corr_id=corr_id)
        _observe(request, metrics, started, status.HTTP_200_OK)
        return summary
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:  # noqa: BLE001
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.get("/breaches", response_model=list[SLABreachResponse])
def list_sla_breaches(
    request: Request,
    response: Response,
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    _user: CurrentUser = Depends(get_current_user),
    service: SLAMetricsService = Depends(get_sla_metrics_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> list[SLABreachResponse]:
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        breaches = service.list_breaches(start_at=start_at, end_at=end_at, corr_id=corr_id)
        _observe(request, metrics, started, status.HTTP_200_OK)
        return breaches
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:  # noqa: BLE001
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


__all__ = ["router"]
