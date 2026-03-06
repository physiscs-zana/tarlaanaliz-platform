# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Farmer payment intent and receipt endpoints."""

from __future__ import annotations

import base64
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from src.presentation.api.dependencies import (
    CancelIntentRequest,
    CurrentUser,
    MetricsCollector,
    PaymentInstructionsResponse,
    PaymentIntentCreateRequest,
    PaymentIntentResponse,
    PaymentService,
    ReceiptUploadRequest,
    get_current_user,
    get_metrics_collector,
    get_payment_service,
)

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}, 409: {"description": "Conflict"}, 422: {"description": "Validation error"}, 429: {"description": "Too many requests"}},
)


def _observe(request: Request, metrics: MetricsCollector, started: float, status_code: int) -> None:
    corr_id = getattr(request.state, "corr_id", None)
    route = request.url.path
    metrics.observe_http(route=route, method=request.method, status_code=status_code, latency_ms=(time.perf_counter() - started) * 1000, corr_id=corr_id)
    metrics.observe_status(route=route, status_code=status_code, corr_id=corr_id)


@router.post("/intents", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_intent(
    payload: PaymentIntentCreateRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    # KR-033: intent creation precedes receipt and approval.
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        intent = service.create_intent(actor_user_id=user.user_id, payload=payload, corr_id=corr_id)
        _observe(request, metrics, started, status.HTTP_201_CREATED)
        return intent
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
        instructions = service.get_payment_instructions(actor_user_id=user.user_id, intent_id=intent_id, corr_id=corr_id)
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
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> PaymentIntentResponse:
    """KR-033 §5: Odeme intent iptal (PAYMENT_PENDING -> CANCELLED)."""
    started = time.perf_counter()
    corr_id = getattr(request.state, "corr_id", None)
    response.headers["X-Correlation-Id"] = corr_id or ""
    try:
        intent = service.cancel_intent(actor_user_id=user.user_id, intent_id=intent_id, reason=payload.reason, corr_id=corr_id)
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
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid receipt encoding") from exc

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


__all__ = ["router"]
