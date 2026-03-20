# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033: Farmer payment intent and receipt management; manual approval flow.
"""Farmer payment intent and receipt endpoints."""

from __future__ import annotations

import base64
import logging
import os
import time
import uuid as _uuid
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from sqlalchemy import select

from src.infrastructure.persistence.sqlalchemy.models.payment_intent_model import PaymentIntentModel
from src.infrastructure.persistence.sqlalchemy.session import get_async_session
from src.presentation.api.dependencies import (
    AuditEvent,
    AuditPublisher,
    CancelIntentRequest,
    CurrentUser,
    MetricsCollector,
    PaymentInstructionsResponse,
    PaymentIntentCreateRequest,
    PaymentIntentResponse,
    PaymentService,
    PaymentStatus,
    ReceiptUploadRequest,
    get_audit_publisher,
    get_current_user,
    get_metrics_collector,
    get_payment_service,
)

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        409: {"description": "Conflict"},
        422: {"description": "Validation error"},
        429: {"description": "Too many requests"},
    },
)


@router.get("/methods")
def get_payment_methods() -> dict[str, object]:
    """Available payment methods — KR-033. Reads from shared pricing config."""
    from src.presentation.api.v1.endpoints.admin_pricing import _read_config

    cfg = _read_config()
    iban = str(cfg.get("iban", "TR33 0006 1005 1978 6457 8413 26"))
    bank = str(cfg.get("bank_name", "Halkbank"))
    recipient = str(cfg.get("recipient", "TarlaAnaliz Tarim Teknolojileri A.S."))

    return {
        "methods": [
            {
                "code": "IBAN",
                "name": "Havale / EFT",
                "available": True,
                "iban": iban,
                "bank_name": bank,
                "recipient": recipient,
            },
            {
                "code": "CREDIT_CARD",
                "name": "Kredi Karti",
                "available": False,
                "message": "SU ANDA SADECE IBAN ILE ODEME ALABILIYORUZ",
            },
        ]
    }


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


@router.post("/intents", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_intent(
    payload: PaymentIntentCreateRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
    audit: AuditPublisher = Depends(get_audit_publisher),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    # KR-033: intent creation precedes receipt and approval.
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        # Use injected service if available (tests); otherwise DB
        svc_registered = getattr(request.app.state, "payment_service", None)
        if svc_registered is not None:
            intent = service.create_intent(actor_user_id=user.user_id, payload=payload, corr_id=corr_id)
            audit.publish(
                AuditEvent(
                    event_type="PAYMENT.INTENT_CREATED",
                    actor_user_id=user.user_id,
                    subject_id=str(intent.intent_id),
                    corr_id=corr_id,
                    details={"status": "PAYMENT_PENDING"},
                )
            )
            _observe(request, metrics, started, status.HTTP_201_CREATED)
            return intent

        now = datetime.now(UTC)
        intent_id = _uuid.uuid4()
        payment_ref = f"PAY-{now.strftime('%Y%m%d')}-{_uuid.uuid4().hex[:6].upper()}"

        async with get_async_session() as session:
            field_id_val = payload.field_ids[0] if payload.field_ids else None

            # Look up existing price_snapshot; None if pricing not yet configured
            import sqlalchemy as sa

            ps_result = await session.execute(sa.text("SELECT price_snapshot_id FROM price_snapshots LIMIT 1"))
            ps_row = ps_result.scalar_one_or_none()

            model = PaymentIntentModel(
                payment_intent_id=intent_id,
                payer_user_id=_uuid.UUID(user.user_id),
                target_type="MISSION",
                target_id=field_id_val or _uuid.uuid4(),
                amount_kurus=int(payload.amount * 100),
                currency="TRY",
                method="IBAN_TRANSFER",
                status="PAYMENT_PENDING",
                payment_ref=payment_ref,
                price_snapshot_id=ps_row,
                created_at=now,
                updated_at=now,
            )
            session.add(model)
            await session.commit()

        intent_resp = PaymentIntentResponse(
            intent_id=intent_id,
            status=PaymentStatus.PENDING_RECEIPT,
            amount=payload.amount,
            season=payload.season,
            package_code=payload.package_code,
            field_ids=payload.field_ids,
            created_at=now,
            payment_ref=payment_ref,
        )
        # KR-033 §8: PAYMENT.INTENT_CREATED audit event
        audit.publish(
            AuditEvent(
                event_type="PAYMENT.INTENT_CREATED",
                actor_user_id=user.user_id,
                subject_id=str(intent_id),
                corr_id=corr_id,
                details={"status": "PAYMENT_PENDING"},
            )
        )
        _observe(request, metrics, started, status.HTTP_201_CREATED)
        return intent_resp
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.get("/intents/{intent_id}/instructions", response_model=PaymentInstructionsResponse)
def get_payment_instructions(
    intent_id: UUID,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentInstructionsResponse:
    """KR-033 §5: Odeme talimatlari (IBAN bilgisi, aciklama formati vb.)."""
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        instructions = service.get_payment_instructions(
            actor_user_id=user.user_id, intent_id=intent_id, corr_id=corr_id
        )
        _observe(request, metrics, started, status.HTTP_200_OK)
        return instructions
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.post("/intents/{intent_id}/cancel", response_model=PaymentIntentResponse)
def cancel_payment_intent(
    intent_id: UUID,
    payload: CancelIntentRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
    audit: AuditPublisher = Depends(get_audit_publisher),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    """KR-033 §5: Odeme intent iptal (PAYMENT_PENDING -> CANCELLED)."""
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        intent = service.cancel_intent(
            actor_user_id=user.user_id, intent_id=intent_id, reason=payload.reason, corr_id=corr_id
        )
        # KR-033 §8: PAYMENT.CANCELLED audit event
        audit.publish(
            AuditEvent(
                event_type="PAYMENT.CANCELLED",
                actor_user_id=user.user_id,
                subject_id=str(intent_id),
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


@router.post("/intents/{intent_id}/upload-receipt", response_model=PaymentIntentResponse)
def upload_receipt(
    intent_id: UUID,
    payload: ReceiptUploadRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    # KR-033: receipt upload required; user cannot set PAID directly.
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        try:
            content = base64.b64decode(payload.content_base64, validate=True)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid receipt encoding"
            ) from exc

        intent = service.upload_receipt(
            actor_user_id=user.user_id,
            intent_id=intent_id,
            filename=payload.filename,
            content_type=payload.content_type,
            content=content,
            corr_id=corr_id,
        )
        _observe(request, metrics, started, status.HTTP_200_OK)
        return intent
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


@router.get("/my-status")
async def get_my_payment_status(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, object]:
    """Farmer payment status summary + analysis schedule (KR-033).

    Returns all payment intents for the current user with status tracking
    and estimated analysis start dates.
    """
    user_id = _uuid.UUID(user.user_id)

    intents: list[dict[str, object]] = []
    try:
        async with get_async_session() as session:
            result = await session.execute(
                select(PaymentIntentModel)
                .where(PaymentIntentModel.payer_user_id == user_id)
                .order_by(PaymentIntentModel.created_at.desc())
            )
            models = result.scalars().all()

            for m in models:
                # Determine status message and analysis schedule
                status_msg = ""
                analysis_info = None
                if m.status == "PAYMENT_PENDING":
                    status_msg = "Odeme bekleniyor. Lutfen EFT/havale yapip dekontu yukleyiniz."
                elif m.status == "PENDING_ADMIN_REVIEW":
                    status_msg = "Dekontunuz inceleniyor. En gec 1 is gunu icinde onaylanacaktir."
                elif m.status == "PAID":
                    status_msg = "Odemeniz onaylandi. Analiz surecine alindiniz."
                    analysis_info = {
                        "message": "Analiz tahmini baslangic: odeme onayi sonrasi 3-7 is gunu.",
                        "estimated_days": 7,
                        "approved_at": m.approved_at.isoformat() if m.approved_at else None,
                    }
                elif m.status == "REJECTED":
                    status_msg = f"Odemeniz reddedildi. Neden: {m.rejected_reason or 'Belirtilmedi'}"
                elif m.status == "CANCELLED":
                    status_msg = "Odeme iptal edildi."
                elif m.status == "REFUNDED":
                    status_msg = "Iadeniz gerceklestirildi."

                intents.append(
                    {
                        "intent_id": str(m.payment_intent_id),
                        "payment_ref": m.payment_ref,
                        "amount_tl": m.amount_kurus / 100.0,
                        "method": m.method,
                        "status": m.status,
                        "status_message": status_msg,
                        "receipt_uploaded": m.receipt_blob_id is not None,
                        "created_at": m.created_at.isoformat(),
                        "analysis_schedule": analysis_info,
                    }
                )
    except Exception:
        pass

    return {
        "user_id": str(user_id),
        "payments": intents,
        "analysis_calendar": {
            "note": "Analiz, odeme onayi sonrasi planlanan ucus takvime gore baslar.",
            "typical_turnaround_days": "3-7 is gunu (ucus + islem)",
        },
    }


@router.get("/{intent_id}", response_model=PaymentIntentResponse)
def get_payment_intent(
    intent_id: UUID,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        intent = service.get_intent(actor_user_id=user.user_id, intent_id=intent_id, corr_id=corr_id)
        _observe(request, metrics, started, status.HTTP_200_OK)
        return intent
    except HTTPException as exc:
        _observe(request, metrics, started, exc.status_code)
        raise
    except Exception as exc:
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


_RECEIPT_DIR_PATHS = ("/app/data/receipts", "data/receipts")
_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
_LOGGER = logging.getLogger("api.payments")


def _receipt_dir() -> str:
    for path in _RECEIPT_DIR_PATHS:
        parent = os.path.dirname(path) or "."
        if os.path.isdir(parent):
            os.makedirs(path, exist_ok=True)
            return path
    os.makedirs(_RECEIPT_DIR_PATHS[0], exist_ok=True)
    return _RECEIPT_DIR_PATHS[0]


@router.post("/upload-receipt")
async def simple_upload_receipt(
    request: Request,
    file: UploadFile = File(...),
    field_id: str = Form(...),
) -> dict[str, str]:
    """Simple receipt upload — saves to filesystem. KR-033."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if file.content_type and file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(status_code=422, detail="Sadece JPEG, PNG, WebP veya PDF yuklenebilir.")

    content = await file.read()
    if len(content) > _MAX_SIZE:
        raise HTTPException(status_code=422, detail="Dosya boyutu 10 MB'dan buyuk olamaz.")

    user_id = getattr(user, "user_id", None) or getattr(user, "subject", "unknown")
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(file.filename or "receipt.jpg")[1] or ".jpg"
    safe_name = f"{field_id[:8]}_{ts}_{_uuid.uuid4().hex[:6]}{ext}"

    receipt_path = os.path.join(_receipt_dir(), safe_name)
    with open(receipt_path, "wb") as f:
        f.write(content)

    _LOGGER.info("RECEIPT.UPLOADED user=%s field=%s file=%s size=%d", user_id, field_id, safe_name, len(content))

    # Update matching payment_intent with receipt_blob_id, or create one if none exists
    now = datetime.now(UTC)
    receipt_meta = {
        "filename": file.filename,
        "size": len(content),
        "content_type": file.content_type,
    }
    try:
        payer_uuid = _uuid.UUID(str(user_id))
    except (ValueError, AttributeError):
        _LOGGER.warning("RECEIPT.INVALID_USER_ID user=%s file=%s", user_id, safe_name)
        return {"status": "uploaded", "filename": safe_name, "message": "Dekont yuklendi. Onay bekleniyor."}

    try:
        field_uuid: _uuid.UUID | None = None
        try:
            field_uuid = _uuid.UUID(field_id)
        except ValueError:
            pass

        async with get_async_session() as session:
            # Try to find existing PAYMENT_PENDING intent for this user
            stmt = (
                select(PaymentIntentModel)
                .where(PaymentIntentModel.payer_user_id == payer_uuid)
                .where(PaymentIntentModel.status.in_(["PAYMENT_PENDING", "PENDING_RECEIPT"]))
                .order_by(PaymentIntentModel.created_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is not None:
                # Link receipt to existing intent
                model.receipt_blob_id = safe_name
                model.receipt_meta = receipt_meta
                model.status = "PENDING_ADMIN_REVIEW"
                model.updated_at = now
                await session.commit()
                _LOGGER.info("RECEIPT.LINKED intent=%s blob=%s", model.payment_intent_id, safe_name)
            else:
                # No existing intent — create one with receipt already attached
                import sqlalchemy as sa
                from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel

                payment_intent_id = _uuid.uuid4()
                payment_ref = f"PAY-{now.strftime('%Y%m%d')}-{_uuid.uuid4().hex[:6].upper()}"

                # Calculate price from field area and pricing config
                amount_kurus = 0
                if field_uuid:
                    try:
                        from src.presentation.api.v1.endpoints.admin_pricing import _read_config

                        field_result = await session.execute(
                            sa.select(FieldModel.area_m2, FieldModel.crop_type).where(FieldModel.field_id == field_uuid)
                        )
                        field_row = field_result.one_or_none()
                        if field_row:
                            cfg = _read_config()
                            crops: list[dict[str, object]] = list(cfg.get("crops", []))  # type: ignore[arg-type]
                            crop_code = field_row.crop_type or "PAMUK"
                            crop_cfg = next((c for c in crops if c.get("code") == crop_code), None)
                            if crop_cfg:
                                area_ha = float(field_row.area_m2) / 10000
                                price_per_ha = crop_cfg.get("single_price", 250)
                                amount_kurus = round(area_ha * price_per_ha * 100)
                    except Exception as exc:
                        _LOGGER.warning("RECEIPT.PRICE_CALC_FAILED field=%s error=%s", field_uuid, exc)

                # Look up price_snapshot if exists
                ps_result = await session.execute(sa.text("SELECT price_snapshot_id FROM price_snapshots LIMIT 1"))
                ps_row = ps_result.scalar_one_or_none()

                new_intent = PaymentIntentModel(
                    payment_intent_id=payment_intent_id,
                    payer_user_id=payer_uuid,
                    target_type="MISSION",
                    target_id=field_uuid or _uuid.uuid4(),
                    amount_kurus=amount_kurus,
                    currency="TRY",
                    method="IBAN_TRANSFER",
                    status="PENDING_ADMIN_REVIEW",
                    payment_ref=payment_ref,
                    price_snapshot_id=ps_row,
                    receipt_blob_id=safe_name,
                    receipt_meta=receipt_meta,
                    created_at=now,
                    updated_at=now,
                )
                session.add(new_intent)
                await session.commit()
                _LOGGER.info(
                    "RECEIPT.CREATED_INTENT intent=%s user=%s blob=%s",
                    payment_intent_id,
                    payer_uuid,
                    safe_name,
                )
    except Exception as exc:
        _LOGGER.error("RECEIPT.LINK_FAILED user=%s file=%s error=%s", user_id, safe_name, exc)

    return {"status": "uploaded", "filename": safe_name, "message": "Dekont yuklendi. Onay bekleniyor."}


__all__ = ["router"]
