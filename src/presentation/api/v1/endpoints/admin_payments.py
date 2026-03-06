# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Admin payment management endpoints."""

from __future__ import annotations

import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from src.presentation.api.dependencies import (
    AuditEvent,
    AuditPublisher,
    CurrentUser,
    MetricsCollector,
    PaymentIntentResponse,
    PaymentService,
    RejectPaymentRequest,
    get_audit_publisher,
    get_metrics_collector,
    get_payment_service,
    require_roles,
    require_permissions,
)

router = APIRouter(
    prefix="/admin/payments",
    tags=["admin-payments"],
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}, 409: {"description": "Conflict"}, 422: {"description": "Validation error"}, 429: {"description": "Too many requests"}},
)


def _observe(request: Request, metrics: MetricsCollector, started: float, status_code: int) -> None:
    corr_id = getattr(request.state, "corr_id", None)
    route = request.url.path
    metrics.observe_http(route=route, method=request.method, status_code=status_code, latency_ms=(time.perf_counter() - started) * 1000, corr_id=corr_id)
    metrics.observe_status(route=route, status_code=status_code, corr_id=corr_id)


@router.get("/pending", response_model=list[PaymentIntentResponse])
def list_pending_payments(
    request: Request,
    response: Response,
    user: CurrentUser = Depends(require_roles(["CENTRAL_ADMIN"])),
    _permissions: CurrentUser = Depends(require_permissions(["payments:review"])),
    payment_service: PaymentService = Depends(get_payment_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> list[PaymentIntentResponse]:
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        records = payment_service.list_pending_payments(corr_id=corr_id)
        _observe(request, metrics, started, status.HTTP_200_OK)
        return records
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:  # noqa: BLE001
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.post("/{payment_id}/approve", response_model=PaymentIntentResponse)
def approve_payment(
    payment_id: UUID,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(require_roles(["CENTRAL_ADMIN"])),
    _permissions: CurrentUser = Depends(require_permissions(["payments:approve"])),
    payment_service: PaymentService = Depends(get_payment_service),
    audit: AuditPublisher = Depends(get_audit_publisher),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    # KR-033: approval and audit required for PAID transition.
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        intent = payment_service.approve_payment(actor_user_id=user.user_id, payment_id=payment_id, corr_id=corr_id)
        audit.publish(
            AuditEvent(
                event_type="payment.approved",
                actor_user_id=user.user_id,
                subject_id=str(payment_id),
                corr_id=corr_id,
                details={"status": intent.status},
            )
        )
        _observe(request, metrics, started, status.HTTP_200_OK)
        return intent
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:  # noqa: BLE001
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.post("/{payment_id}/reject", response_model=PaymentIntentResponse)
def reject_payment(
    payment_id: UUID,
    payload: RejectPaymentRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(require_roles(["CENTRAL_ADMIN"])),
    _permissions: CurrentUser = Depends(require_permissions(["payments:reject"])),
    payment_service: PaymentService = Depends(get_payment_service),
    audit: AuditPublisher = Depends(get_audit_publisher),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    # KR-033: rejection reason must be audit logged.
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        intent = payment_service.reject_payment(actor_user_id=user.user_id, payment_id=payment_id, reason=payload.reason, corr_id=corr_id)
        audit.publish(
            AuditEvent(
                event_type="payment.rejected",
                actor_user_id=user.user_id,
                subject_id=str(payment_id),
                corr_id=corr_id,
                details={"reason": payload.reason, "status": intent.status},
            )
        )
        _observe(request, metrics, started, status.HTTP_200_OK)
        return intent
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:  # noqa: BLE001
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


__all__ = ["router"]
