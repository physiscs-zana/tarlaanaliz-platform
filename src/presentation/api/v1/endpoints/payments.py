# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033: Farmer payment intent and receipt management; manual approval flow.
"""Farmer payment intent and receipt endpoints."""

from __future__ import annotations

import base64
import logging
import os
import time
import uuid as _uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

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
    audit: AuditPublisher = Depends(get_audit_publisher),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    # KR-033: intent creation precedes receipt and approval.
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        now = datetime.now(timezone.utc)
        intent_id = _uuid.uuid4()
        payment_ref = f"PAY-{now.strftime('%Y%m%d')}-{_uuid.uuid4().hex[:6].upper()}"

        # Find a valid price_snapshot_id for FK constraint
        from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel

        async with get_async_session() as session:
            # Get first field's info for price_snapshot lookup
            price_snapshot_id = _uuid.uuid4()  # Placeholder — will be replaced when pricing is wired
            field_id_val = payload.field_ids[0] if payload.field_ids else None

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
                price_snapshot_id=price_snapshot_id,
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
    except Exception as exc:  # noqa: BLE001
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
    except Exception as exc:  # noqa: BLE001
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
    except Exception as exc:  # noqa: BLE001
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
    except Exception as exc:  # noqa: BLE001
        _observe(request, metrics, started, status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc


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
    except Exception as exc:  # noqa: BLE001
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
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(file.filename or "receipt.jpg")[1] or ".jpg"
    safe_name = f"{field_id[:8]}_{ts}_{_uuid.uuid4().hex[:6]}{ext}"

    receipt_path = os.path.join(_receipt_dir(), safe_name)
    with open(receipt_path, "wb") as f:
        f.write(content)

    _LOGGER.info("RECEIPT.UPLOADED user=%s field=%s file=%s size=%d", user_id, field_id, safe_name, len(content))

    # Update matching payment_intent with receipt_blob_id (find by payer + PAYMENT_PENDING status)
    try:
        async with get_async_session() as session:
            stmt = (
                select(PaymentIntentModel)
                .where(PaymentIntentModel.payer_user_id == _uuid.UUID(str(user_id)))
                .where(PaymentIntentModel.status == "PAYMENT_PENDING")
                .order_by(PaymentIntentModel.created_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if model is not None:
                model.receipt_blob_id = safe_name
                model.receipt_meta = {
                    "filename": file.filename,
                    "size": len(content),
                    "content_type": file.content_type,
                }
                model.status = "PENDING_ADMIN_REVIEW"
                model.updated_at = datetime.now(timezone.utc)
                await session.commit()
                _LOGGER.info("RECEIPT.LINKED intent=%s blob=%s", model.payment_intent_id, safe_name)
    except Exception:
        _LOGGER.warning("RECEIPT.LINK_FAILED user=%s file=%s — no matching intent found", user_id, safe_name)

    return {"status": "uploaded", "filename": safe_name, "message": "Dekont yuklendi. Onay bekleniyor."}


__all__ = ["router"]
