# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033 §5: Admin ödeme yönetim endpoint'leri.
# KR-033 §8: Audit event isimleri: PAYMENT.MARK_PAID, PAYMENT.REJECTED, PAYMENT.REFUNDED.
# KR-033 §10: Geri ödeme limit politikası — ≤500 TL BILLING_ADMIN, >500 TL CENTRAL_ADMIN.
# KR-063: RBAC rolleri — CENTRAL_ADMIN, BILLING_ADMIN.
"""Admin payment management endpoints (KR-033 §5)."""

from __future__ import annotations

import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from src.presentation.api.dependencies import (
    AuditEvent,
    AuditPublisher,
    CurrentUser,
    MarkPaidRequest,
    MetricsCollector,
    PaymentIntentResponse,
    PaymentService,
    RefundPaymentRequest,
    RejectPaymentRequest,
    get_audit_publisher,
    get_metrics_collector,
    get_payment_service,
    require_permissions,
    require_roles,
)

# KR-033 §10: Geri ödeme eşiği — 500 TL = 50000 kuruş
_REFUND_APPROVAL_THRESHOLD_KURUS = 50000

router = APIRouter(
    prefix="/admin/payments",
    tags=["admin-payments"],
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


@router.get("/intents", response_model=list[PaymentIntentResponse])
def list_payment_intents(
    request: Request,
    response: Response,
    status_filter: str | None = Query(default=None, alias="status"),
    field_id: UUID | None = Query(default=None),
    user: CurrentUser = Depends(require_roles(["CENTRAL_ADMIN", "BILLING_ADMIN"])),
    _permissions: CurrentUser = Depends(require_permissions(["payments:review"])),
    payment_service: PaymentService = Depends(get_payment_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> list[PaymentIntentResponse]:
    """KR-033 §5: Bekleyen tahsilatlar; status ve field_id ile filtreleme."""
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        # Translate frontend PAYMENT_PENDING to internal statuses
        if status_filter == "PAYMENT_PENDING":
            records_a = payment_service.list_intents(
                status_filter="PENDING_RECEIPT", field_id=field_id, corr_id=corr_id
            )
            records_b = payment_service.list_intents(
                status_filter="PENDING_ADMIN_REVIEW", field_id=field_id, corr_id=corr_id
            )
            seen: set[str] = set()
            records = []
            for r in [*records_a, *records_b]:
                pid = getattr(r, "payment_id", id(r))
                if pid not in seen:
                    seen.add(pid)
                    records.append(r)
        else:
            records = payment_service.list_intents(status_filter=status_filter, field_id=field_id, corr_id=corr_id)
        _observe(request, metrics, started, status.HTTP_200_OK)
        return records
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.post("/intents/{payment_id}/mark-paid", response_model=PaymentIntentResponse)
def mark_paid(
    payment_id: UUID,
    payload: MarkPaidRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(require_roles(["CENTRAL_ADMIN", "BILLING_ADMIN"])),
    _permissions: CurrentUser = Depends(require_permissions(["payments:approve"])),
    payment_service: PaymentService = Depends(get_payment_service),
    audit: AuditPublisher = Depends(get_audit_publisher),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    """KR-033 §5: Manuel ödeme onayı. admin_note zorunlu (KR-033 §8)."""
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        intent = payment_service.approve_payment(
            actor_user_id=user.user_id,
            payment_id=payment_id,
            admin_note=payload.admin_note,
            corr_id=corr_id,
        )
        # KR-033 §8: PAYMENT.MARK_PAID audit event — admin_user_id ve admin_note zorunlu
        audit.publish(
            AuditEvent(
                event_type="PAYMENT.MARK_PAID",
                actor_user_id=user.user_id,
                subject_id=str(payment_id),
                corr_id=corr_id,
                details={"status": intent.status, "admin_note": payload.admin_note},
            )
        )
        _observe(request, metrics, started, status.HTTP_200_OK)
        return intent
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.post("/intents/{payment_id}/reject", response_model=PaymentIntentResponse)
def reject_payment(
    payment_id: UUID,
    payload: RejectPaymentRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(require_roles(["CENTRAL_ADMIN", "BILLING_ADMIN"])),
    _permissions: CurrentUser = Depends(require_permissions(["payments:reject"])),
    payment_service: PaymentService = Depends(get_payment_service),
    audit: AuditPublisher = Depends(get_audit_publisher),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    """KR-033 §5: Ödeme reddi. rejection_reason zorunlu."""
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        intent = payment_service.reject_payment(
            actor_user_id=user.user_id, payment_id=payment_id, reason=payload.reason, corr_id=corr_id
        )
        # KR-033 §8: PAYMENT.REJECTED audit event
        audit.publish(
            AuditEvent(
                event_type="PAYMENT.REJECTED",
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
    except Exception as exc:
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.post("/intents/{payment_id}/refund", response_model=PaymentIntentResponse)
def refund_payment(
    payment_id: UUID,
    payload: RefundPaymentRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(require_roles(["CENTRAL_ADMIN", "BILLING_ADMIN"])),
    _permissions: CurrentUser = Depends(require_permissions(["payments:refund"])),
    payment_service: PaymentService = Depends(get_payment_service),
    audit: AuditPublisher = Depends(get_audit_publisher),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    """KR-033 §5: İade (PAID → REFUNDED). KR-033 §10: >500 TL ise CENTRAL_ADMIN zorunlu."""
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        # KR-033 §10: Geri ödeme limit politikası
        if payload.refund_amount_kurus > _REFUND_APPROVAL_THRESHOLD_KURUS:
            if "CENTRAL_ADMIN" not in user.roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Refunds exceeding 500 TL require CENTRAL_ADMIN approval (KR-033 §10)",
                )

        intent = payment_service.refund_payment(
            actor_user_id=user.user_id,
            payment_id=payment_id,
            refund_amount_kurus=payload.refund_amount_kurus,
            reason=payload.reason,
            corr_id=corr_id,
        )
        # KR-033 §8: PAYMENT.REFUNDED audit event
        audit.publish(
            AuditEvent(
                event_type="PAYMENT.REFUNDED",
                actor_user_id=user.user_id,
                subject_id=str(payment_id),
                corr_id=corr_id,
                details={
                    "refund_amount_kurus": payload.refund_amount_kurus,
                    "reason": payload.reason,
                    "status": intent.status,
                },
            )
        )
        _observe(request, metrics, started, status.HTTP_200_OK)
        return intent
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


__all__ = ["router"]
