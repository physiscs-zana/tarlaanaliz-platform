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
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.infrastructure.persistence.sqlalchemy.models.payment_intent_model import PaymentIntentModel
from src.infrastructure.persistence.sqlalchemy.session import get_async_session
from src.presentation.api.dependencies import (
    AuditEvent,
    AuditPublisher,
    CurrentUser,
    MarkPaidRequest,
    MetricsCollector,
    PaymentIntentResponse,
    PaymentService,
    PaymentStatus,
    RefundPaymentRequest,
    RejectPaymentRequest,
    get_audit_publisher,
    get_metrics_collector,
    get_payment_service,
    require_permissions,
    require_roles,
)


def _get_service(request: Request) -> PaymentService | None:
    """Return registered payment service if available (test/DI), else None (use DB)."""
    svc: PaymentService | None = getattr(request.app.state, "payment_service", None)
    return svc


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


def _model_to_response(m: PaymentIntentModel) -> PaymentIntentResponse:
    """Convert ORM model to API response."""
    payer_name = None
    if m.payer:
        payer_name = m.payer.display_name or f"{m.payer.first_name} {m.payer.last_name}".strip() or None
    return PaymentIntentResponse(
        intent_id=m.payment_intent_id,
        status=PaymentStatus(m.status)
        if m.status in PaymentStatus.__members__.values()
        else PaymentStatus.PENDING_RECEIPT,
        amount=m.amount_kurus / 100.0,
        season="",
        package_code=m.method or "",
        field_ids=[],
        created_at=m.created_at,
        receipt_blob_id=m.receipt_blob_id,
        payer_display_name=payer_name,
        payment_ref=m.payment_ref,
    )


@router.get("/intents", response_model=list[PaymentIntentResponse])
async def list_payment_intents(
    request: Request,
    response: Response,
    status_filter: str | None = Query(default=None, alias="status"),
    field_id: UUID | None = Query(default=None),
    user: CurrentUser = Depends(require_roles(["CENTRAL_ADMIN", "BILLING_ADMIN"])),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> list[PaymentIntentResponse]:
    """KR-033 §5: Bekleyen tahsilatlar; status ve field_id ile filtreleme."""
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        svc = _get_service(request)
        if svc is not None:
            records = svc.list_intents(status_filter=status_filter, field_id=field_id, corr_id=corr_id)
            _observe(request, metrics, started, status.HTTP_200_OK)
            return records

        async with get_async_session() as session:
            stmt = select(PaymentIntentModel).options(selectinload(PaymentIntentModel.payer))

            if status_filter == "PAYMENT_PENDING":
                stmt = stmt.where(
                    PaymentIntentModel.status.in_(["PAYMENT_PENDING", "PENDING_RECEIPT", "PENDING_ADMIN_REVIEW"])
                )
            elif status_filter:
                stmt = stmt.where(PaymentIntentModel.status == status_filter)

            stmt = stmt.order_by(PaymentIntentModel.created_at.desc())
            result = await session.execute(stmt)
            models = result.scalars().unique().all()

        records = [_model_to_response(m) for m in models]
        _observe(request, metrics, started, status.HTTP_200_OK)
        return records
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.post("/intents/{payment_id}/mark-paid", response_model=PaymentIntentResponse)
async def mark_paid(
    payment_id: UUID,
    payload: MarkPaidRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(require_roles(["CENTRAL_ADMIN", "BILLING_ADMIN"])),
    audit: AuditPublisher = Depends(get_audit_publisher),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    """KR-033 §5: Manuel ödeme onayı. admin_note zorunlu (KR-033 §8)."""
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        svc = _get_service(request)
        if svc is not None:
            intent = svc.approve_payment(
                actor_user_id=user.user_id, payment_id=payment_id, admin_note=payload.admin_note, corr_id=corr_id
            )
            audit.publish(
                AuditEvent(
                    event_type="PAYMENT.MARK_PAID",
                    actor_user_id=user.user_id,
                    subject_id=str(payment_id),
                    corr_id=corr_id,
                    details={"status": "PAID", "admin_note": payload.admin_note},
                )
            )
            _observe(request, metrics, started, status.HTTP_200_OK)
            return intent

        from datetime import datetime, timezone

        async with get_async_session() as session:
            result = await session.execute(
                select(PaymentIntentModel)
                .options(selectinload(PaymentIntentModel.payer))
                .where(PaymentIntentModel.payment_intent_id == payment_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                raise HTTPException(status_code=404, detail="Payment intent not found")

            model.status = "PAID"
            model.paid_at = datetime.now(timezone.utc)
            model.approved_by_admin_user_id = UUID(user.user_id)
            model.approved_at = model.paid_at
            model.admin_note = payload.admin_note
            model.updated_at = datetime.now(timezone.utc)
            await session.commit()

        audit.publish(
            AuditEvent(
                event_type="PAYMENT.MARK_PAID",
                actor_user_id=user.user_id,
                subject_id=str(payment_id),
                corr_id=corr_id,
                details={"status": "PAID", "admin_note": payload.admin_note},
            )
        )
        _observe(request, metrics, started, status.HTTP_200_OK)
        return _model_to_response(model)
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.post("/intents/{payment_id}/reject", response_model=PaymentIntentResponse)
async def reject_payment(
    payment_id: UUID,
    payload: RejectPaymentRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(require_roles(["CENTRAL_ADMIN", "BILLING_ADMIN"])),
    audit: AuditPublisher = Depends(get_audit_publisher),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    """KR-033 §5: Ödeme reddi. rejection_reason zorunlu."""
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        svc = _get_service(request)
        if svc is not None:
            intent = svc.reject_payment(
                actor_user_id=user.user_id, payment_id=payment_id, reason=payload.reason, corr_id=corr_id
            )
            audit.publish(
                AuditEvent(
                    event_type="PAYMENT.REJECTED",
                    actor_user_id=user.user_id,
                    subject_id=str(payment_id),
                    corr_id=corr_id,
                    details={"reason": payload.reason, "status": "REJECTED"},
                )
            )
            _observe(request, metrics, started, status.HTTP_200_OK)
            return intent

        from datetime import datetime, timezone

        async with get_async_session() as session:
            result = await session.execute(
                select(PaymentIntentModel)
                .options(selectinload(PaymentIntentModel.payer))
                .where(PaymentIntentModel.payment_intent_id == payment_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                raise HTTPException(status_code=404, detail="Payment intent not found")

            model.status = "REJECTED"
            model.rejected_at = datetime.now(timezone.utc)
            model.rejected_reason = payload.reason
            model.updated_at = datetime.now(timezone.utc)
            await session.commit()

        audit.publish(
            AuditEvent(
                event_type="PAYMENT.REJECTED",
                actor_user_id=user.user_id,
                subject_id=str(payment_id),
                corr_id=corr_id,
                details={"reason": payload.reason, "status": "REJECTED"},
            )
        )
        _observe(request, metrics, started, status.HTTP_200_OK)
        return _model_to_response(model)
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.post("/intents/{payment_id}/refund", response_model=PaymentIntentResponse)
async def refund_payment(
    payment_id: UUID,
    payload: RefundPaymentRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(require_roles(["CENTRAL_ADMIN", "BILLING_ADMIN"])),
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

        svc = _get_service(request)
        if svc is not None:
            intent = svc.refund_payment(
                actor_user_id=user.user_id,
                payment_id=payment_id,
                refund_amount_kurus=payload.refund_amount_kurus,
                reason=payload.reason,
                corr_id=corr_id,
            )
            audit.publish(
                AuditEvent(
                    event_type="PAYMENT.REFUNDED",
                    actor_user_id=user.user_id,
                    subject_id=str(payment_id),
                    corr_id=corr_id,
                    details={
                        "refund_amount_kurus": payload.refund_amount_kurus,
                        "reason": payload.reason,
                        "status": "REFUNDED",
                    },
                )
            )
            _observe(request, metrics, started, status.HTTP_200_OK)
            return intent

        from datetime import datetime, timezone

        async with get_async_session() as session:
            result = await session.execute(
                select(PaymentIntentModel)
                .options(selectinload(PaymentIntentModel.payer))
                .where(PaymentIntentModel.payment_intent_id == payment_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                raise HTTPException(status_code=404, detail="Payment intent not found")
            if model.status != "PAID":
                raise HTTPException(status_code=409, detail=f"Can only refund PAID intents, current: {model.status}")

            model.status = "REFUNDED"
            model.refunded_at = datetime.now(timezone.utc)
            model.refund_amount_kurus = payload.refund_amount_kurus
            model.refund_reason = payload.reason
            model.updated_at = datetime.now(timezone.utc)
            await session.commit()

        audit.publish(
            AuditEvent(
                event_type="PAYMENT.REFUNDED",
                actor_user_id=user.user_id,
                subject_id=str(payment_id),
                corr_id=corr_id,
                details={
                    "refund_amount_kurus": payload.refund_amount_kurus,
                    "reason": payload.reason,
                    "status": "REFUNDED",
                },
            )
        )
        _observe(request, metrics, started, status.HTTP_200_OK)
        return _model_to_response(model)
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


__all__ = ["router"]
