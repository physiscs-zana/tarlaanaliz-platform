# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033 §5: Admin ödeme yönetim endpoint'leri.
# KR-033 §8: Audit event isimleri: PAYMENT.MARK_PAID, PAYMENT.REJECTED, PAYMENT.REFUNDED.
# KR-033 §10: Geri ödeme limit politikası — ≤500 TL BILLING_ADMIN, >500 TL CENTRAL_ADMIN.
# KR-063: RBAC rolleri — CENTRAL_ADMIN, BILLING_ADMIN.
"""Admin payment management endpoints (KR-033 §5)."""

from __future__ import annotations

import logging
import os
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse
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


def _model_to_response(
    m: PaymentIntentModel,
    *,
    field_info: dict[str, dict[str, object]] | None = None,
) -> PaymentIntentResponse:
    """Convert ORM model to API response with T+1 SLA calculation.

    field_info: {target_id_str: {"crop_type": ..., "area_donum": ..., "field_name": ...}}
    """
    from datetime import datetime, timedelta, timezone

    payer_name = None
    if m.payer:
        payer_name = m.payer.display_name or f"{m.payer.first_name} {m.payer.last_name}".strip() or None

    # T+1 SLA: receipt upload time + 1 business day (17:00)
    sla_deadline = None
    sla_overdue = False
    if m.status == "PENDING_ADMIN_REVIEW" and m.updated_at:
        # Deadline: next business day 17:00 after receipt upload
        receipt_time = m.updated_at
        deadline = receipt_time + timedelta(days=1)
        # Skip weekends
        while deadline.weekday() >= 5:  # Saturday=5, Sunday=6
            deadline += timedelta(days=1)
        deadline = deadline.replace(hour=17, minute=0, second=0, microsecond=0)
        sla_deadline = deadline.isoformat()
        sla_overdue = datetime.now(timezone.utc) > deadline

    payer_phone = None
    payer_province = None
    payer_district = None
    if m.payer:
        payer_phone = m.payer.phone
        payer_province = m.payer.province
        payer_district = m.payer.district

    # KR-033: Analiz detayları — target_type, crop_type, area_donum, field_name
    target_type = m.target_type
    crop_type = None
    area_donum = None
    field_name = None
    if field_info and str(m.target_id) in field_info:
        fi = field_info[str(m.target_id)]
        crop_type = str(fi.get("crop_type", "")) or None
        raw_area = fi.get("area_donum")
        area_donum = float(str(raw_area)) if raw_area is not None else None
        field_name = str(fi.get("field_name", "")) or None

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
        payer_phone=payer_phone,
        payer_province=payer_province,
        payer_district=payer_district,
        payment_ref=m.payment_ref,
        sla_deadline=sla_deadline,
        sla_overdue=sla_overdue,
        target_type=target_type,
        crop_type=crop_type,
        area_donum=area_donum,
        field_name=field_name,
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

            # KR-033: Toplu field bilgisi lookup — analiz türü, bitki, tarla boyutu
            field_info: dict[str, dict[str, object]] = {}
            from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel
            from src.infrastructure.persistence.sqlalchemy.models.mission_model import MissionModel
            from src.infrastructure.persistence.sqlalchemy.models.subscription_model import SubscriptionModel

            mission_target_ids = [m.target_id for m in models if m.target_type == "MISSION"]
            sub_target_ids = [m.target_id for m in models if m.target_type == "SUBSCRIPTION"]

            # Mission → field bilgisi
            if mission_target_ids:
                m_result = await session.execute(
                    select(
                        MissionModel.mission_id,
                        MissionModel.crop_type,
                        FieldModel.area_donum,
                        FieldModel.field_code,
                    )
                    .join(FieldModel, MissionModel.field_id == FieldModel.field_id)
                    .where(MissionModel.mission_id.in_(mission_target_ids))
                )
                for row in m_result.all():
                    field_info[str(row.mission_id)] = {
                        "crop_type": row.crop_type,
                        "area_donum": row.area_donum,
                        "field_name": row.field_code,
                    }

            # Subscription → field bilgisi
            if sub_target_ids:
                s_result = await session.execute(
                    select(
                        SubscriptionModel.subscription_id,
                        SubscriptionModel.crop_type,
                        FieldModel.area_donum,
                        FieldModel.field_code,
                    )
                    .join(FieldModel, SubscriptionModel.field_id == FieldModel.field_id)
                    .where(SubscriptionModel.subscription_id.in_(sub_target_ids))
                )
                for row in s_result.all():
                    field_info[str(row.subscription_id)] = {
                        "crop_type": row.crop_type,
                        "area_donum": row.area_donum,
                        "field_name": row.field_code,
                    }

        records = [_model_to_response(m, field_info=field_info) for m in models]
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
            if model.status == "PAID":
                _observe(request, metrics, started, status.HTTP_200_OK)
                return _model_to_response(model)  # Idempotent: already paid

            model.status = "PAID"
            model.paid_at = datetime.now(timezone.utc)
            model.approved_by_admin_user_id = UUID(user.user_id)
            model.approved_at = model.paid_at
            model.admin_note = payload.admin_note
            model.updated_at = datetime.now(timezone.utc)

            # KR-033 + KR-015: Auto-dispatch pilot after payment approval
            if model.target_type == "MISSION" and model.target_id:
                from src.infrastructure.persistence.sqlalchemy.models.mission_model import MissionModel
                from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel
                from src.infrastructure.persistence.sqlalchemy.models.pilot_model import (
                    MissionAssignmentModel,
                    PilotModel,
                    PilotServiceAreaModel,
                )

                mission_result = await session.execute(
                    select(MissionModel).where(MissionModel.mission_id == model.target_id)
                )
                mission = mission_result.scalar_one_or_none()

                if mission and mission.status == "PLANNED":
                    # Look up field province for region matching
                    field_province = None
                    field_area_donum = 0
                    field_result = await session.execute(
                        select(FieldModel.province, FieldModel.area_donum).where(
                            FieldModel.field_id == mission.field_id
                        )
                    )
                    field_row = field_result.one_or_none()
                    if field_row:
                        field_province = field_row.province
                        field_area_donum = int(field_row.area_donum)

                    # Find eligible pilots: active + matching province via service_areas
                    assigned_pilot_id = None
                    if field_province:
                        pilot_stmt = (
                            select(PilotModel)
                            .join(PilotServiceAreaModel, PilotModel.pilot_id == PilotServiceAreaModel.pilot_id)
                            .where(PilotModel.is_active.is_(True))
                            .where(PilotServiceAreaModel.province == field_province)
                            .order_by(PilotModel.reliability_score.desc())
                        )
                        pilot_result = await session.execute(pilot_stmt)
                        eligible_pilots = pilot_result.scalars().unique().all()

                        # Pick first pilot with enough capacity
                        for pilot in eligible_pilots:
                            if pilot.daily_capacity_donum >= field_area_donum:
                                assigned_pilot_id = pilot.pilot_id
                                # Create mission_assignment record
                                assignment = MissionAssignmentModel(
                                    mission_id=model.target_id,
                                    pilot_id=pilot.pilot_id,
                                    assignment_type="SYSTEM_SEED",
                                    is_current=True,
                                )
                                session.add(assignment)
                                break

                    # KR-028: Mission status geçişi — pilot varsa ASSIGNED, yoksa PLANNED kalır
                    if assigned_pilot_id:
                        mission.status = "ASSIGNED"
                        _RECEIPT_LOGGER.warning(
                            "MISSION.AUTO_DISPATCHED mission=%s pilot=%s payment=%s province=%s",
                            model.target_id,
                            assigned_pilot_id,
                            payment_id,
                            field_province,
                        )
                    else:
                        # KR-028: Pilot bulunamadığında mission PLANNED kalır, admin manuel atayacak
                        _RECEIPT_LOGGER.warning(
                            "MISSION.PAID_NO_PILOT mission=%s payment=%s province=%s — pilot bulunamadi, PLANNED olarak kaliyor",
                            model.target_id,
                            payment_id,
                            field_province,
                        )

            # KR-027 + KR-033: Activate subscription and create first mission after payment
            elif model.target_type == "SUBSCRIPTION" and model.target_id:
                from src.infrastructure.persistence.sqlalchemy.models.subscription_model import SubscriptionModel
                from src.infrastructure.persistence.sqlalchemy.models.mission_model import MissionModel
                from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel
                from src.infrastructure.persistence.sqlalchemy.models.pilot_model import (
                    MissionAssignmentModel,
                    PilotModel,
                    PilotServiceAreaModel,
                )
                import uuid as _uuid

                sub_result = await session.execute(
                    select(SubscriptionModel).where(SubscriptionModel.subscription_id == model.target_id)
                )
                subscription = sub_result.scalar_one_or_none()

                if subscription and subscription.status == "PENDING_PAYMENT":
                    subscription.status = "ACTIVE"

                    # Create the first mission from subscription data
                    first_mission_id = _uuid.uuid4()
                    planned_at = subscription.next_due_at or datetime.combine(
                        subscription.start_date, datetime.min.time()
                    ).replace(tzinfo=timezone.utc)

                    first_mission = MissionModel(
                        mission_id=first_mission_id,
                        field_id=subscription.field_id,
                        requested_by_user_id=subscription.farmer_user_id,
                        subscription_id=subscription.subscription_id,
                        payment_intent_id=model.payment_intent_id,
                        crop_type=subscription.crop_type,
                        analysis_type=subscription.analysis_type or "MULTISPECTRAL",
                        status="PLANNED",
                        planned_at=planned_at,
                        created_at=datetime.now(timezone.utc),
                    )
                    session.add(first_mission)

                    # Auto-dispatch pilot (same logic as MISSION flow)
                    field_result = await session.execute(
                        select(FieldModel.province, FieldModel.area_donum).where(
                            FieldModel.field_id == subscription.field_id
                        )
                    )
                    field_row = field_result.one_or_none()
                    assigned_pilot_id = None
                    field_province = None

                    if field_row:
                        field_province = field_row.province
                        field_area_donum = int(field_row.area_donum)

                        if field_province:
                            pilot_stmt = (
                                select(PilotModel)
                                .join(PilotServiceAreaModel, PilotModel.pilot_id == PilotServiceAreaModel.pilot_id)
                                .where(PilotModel.is_active.is_(True))
                                .where(PilotServiceAreaModel.province == field_province)
                                .order_by(PilotModel.reliability_score.desc())
                            )
                            pilot_result = await session.execute(pilot_stmt)
                            eligible_pilots = pilot_result.scalars().unique().all()

                            for pilot in eligible_pilots:
                                if pilot.daily_capacity_donum >= field_area_donum:
                                    assigned_pilot_id = pilot.pilot_id
                                    assignment = MissionAssignmentModel(
                                        mission_id=first_mission_id,
                                        pilot_id=pilot.pilot_id,
                                        assignment_type="SYSTEM_SEED",
                                        is_current=True,
                                    )
                                    session.add(assignment)
                                    break

                    # KR-028: Pilot varsa mission ASSIGNED'a geçir
                    if assigned_pilot_id:
                        first_mission.status = "ASSIGNED"

                    _RECEIPT_LOGGER.warning(
                        "SUBSCRIPTION.ACTIVATED sub=%s mission=%s pilot=%s payment=%s province=%s status=%s",
                        model.target_id,
                        first_mission_id,
                        assigned_pilot_id,
                        payment_id,
                        field_province,
                        first_mission.status,
                    )

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


_RECEIPT_DIR_PATHS = ("/app/data/receipts", "data/receipts")
_RECEIPT_LOGGER = logging.getLogger("api.admin_payments")


def _find_receipt_path(blob_id: str) -> str | None:
    """Locate receipt file on disk. Returns absolute path or None."""
    # Prevent path traversal
    safe_name = os.path.basename(blob_id)
    if safe_name != blob_id or ".." in blob_id:
        return None
    for base in _RECEIPT_DIR_PATHS:
        candidate = os.path.join(base, safe_name)
        if os.path.isfile(candidate):
            return candidate
    return None


_CONTENT_TYPE_MAP: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}


@router.get("/receipts/{blob_id}")
async def view_receipt(
    blob_id: str,
    request: Request,
    user: CurrentUser = Depends(require_roles(["CENTRAL_ADMIN", "BILLING_ADMIN"])),
) -> FileResponse:
    """KR-033: Admin dekont görüntüleme — dosyayı disk'ten serve eder."""
    file_path = _find_receipt_path(blob_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Dekont dosyasi bulunamadi")

    ext = os.path.splitext(blob_id)[1].lower()
    media_type = _CONTENT_TYPE_MAP.get(ext, "application/octet-stream")

    _RECEIPT_LOGGER.info(
        "RECEIPT.VIEWED admin=%s blob=%s",
        user.user_id,
        blob_id,
    )

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=blob_id,
    )


__all__ = ["router"]
