# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""FastAPI application entrypoint and wiring."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Callable

from fastapi import FastAPI, Request
from starlette.responses import Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.presentation.api.middleware.anomaly_detection_middleware import AnomalyDetectionMiddleware
from src.presentation.api.middleware.cors_middleware import add_cors_middleware
from src.presentation.api.middleware.grid_anonymizer import GridAnonymizerMiddleware
from src.presentation.api.middleware.jwt_middleware import JwtMiddleware
from src.presentation.api.middleware.mtls_verifier import MTLSVerifierMiddleware
from src.presentation.api.middleware.pii_filter import PIIFilterMiddleware
from src.presentation.api.middleware.rate_limit_middleware import RateLimitMiddleware
from src.presentation.api.settings import settings
from src.presentation.api.v1.endpoints import (
    admin_audit_router,
    admin_payments_router,
    admin_pricing_router,
    auth_router,
    calibration_router,
    expert_portal_router,
    experts_router,
    fields_router,
    missions_router,
    parcels_router,
    payment_webhooks_router,
    payments_router,
    pilots_router,
    pricing_router,
    qc_router,
    results_router,
    sla_metrics_router,
    subscriptions_router,
    training_feedback_router,
    weather_block_reports_router,
    weather_blocks_router,
)


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Lifecycle hooks for startup/shutdown tasks."""
    yield


async def _corr_id_middleware(request: Request, call_next: Callable[..., Any]) -> Response:
    corr_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
    request.state.corr_id = corr_id
    response: Response = await call_next(request)
    response.headers["X-Correlation-Id"] = corr_id
    return response


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, _: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": "Validation failed", "corr_id": getattr(request.state, "corr_id", None)},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        safe_detail = exc.detail if exc.status_code < 500 else "Internal server error"
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": safe_detail, "corr_id": getattr(request.state, "corr_id", None)},
        )

    @app.exception_handler(Exception)
    async def handle_uncaught_exception(request: Request, _: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "corr_id": getattr(request.state, "corr_id", None)},
        )


def create_app() -> FastAPI:
    """Create and configure the FastAPI app instance."""
    app = FastAPI(
        title=settings.app.title,
        version=settings.app.version,
        docs_url=settings.app.docs_url,
        redoc_url=settings.app.redoc_url,
        openapi_url=settings.app.openapi_url,
        lifespan=_lifespan,
    )

    # Middleware stack (LIFO order — last added executes first):
    # 1. Correlation ID (http middleware — outermost)
    # 2. CORS
    # 3. mTLS Verifier (KR-071 — before auth for ingest endpoints)
    # 4. JWT Authentication
    # 5. Rate Limiting
    # 6. Anomaly Detection
    # 7. PII Filter (KR-066 — after auth, before response)
    # 8. Grid Anonymizer (KR-083 — after auth, before response)
    app.middleware("http")(_corr_id_middleware)
    add_cors_middleware(app)
    app.add_middleware(MTLSVerifierMiddleware)
    app.add_middleware(JwtMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AnomalyDetectionMiddleware)
    app.add_middleware(PIIFilterMiddleware)
    app.add_middleware(GridAnonymizerMiddleware)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(payments_router, prefix="/api/v1")
    app.include_router(admin_payments_router, prefix="/api/v1")
    app.include_router(calibration_router, prefix="/api/v1")
    app.include_router(qc_router, prefix="/api/v1")
    app.include_router(sla_metrics_router, prefix="/api/v1")

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(fields_router, prefix="/api/v1")
    app.include_router(parcels_router, prefix="/api/v1")
    app.include_router(missions_router, prefix="/api/v1")
    app.include_router(experts_router, prefix="/api/v1")
    app.include_router(expert_portal_router, prefix="/api/v1")
    app.include_router(payment_webhooks_router, prefix="/api/v1")
    app.include_router(admin_audit_router, prefix="/api/v1")
    app.include_router(admin_pricing_router, prefix="/api/v1")
    app.include_router(pilots_router, prefix="/api/v1")
    app.include_router(pricing_router, prefix="/api/v1")
    app.include_router(results_router, prefix="/api/v1")
    app.include_router(subscriptions_router, prefix="/api/v1")
    app.include_router(training_feedback_router, prefix="/api/v1")
    app.include_router(weather_block_reports_router, prefix="/api/v1")
    app.include_router(weather_blocks_router, prefix="/api/v1")

    _register_exception_handlers(app)
    return app


app = create_app()

__all__ = ["app", "create_app"]
