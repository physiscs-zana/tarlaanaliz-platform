# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: FastAPI application entrypoint and wiring.
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
from src.presentation.api.middleware.rbac_middleware import RBACMiddleware
from src.presentation.api.middleware.rate_limit_middleware import RateLimitMiddleware
from src.presentation.api.settings import settings
from src.presentation.api.v1.endpoints import (
    admin_audit_router,
    admin_dashboard_router,
    admin_payments_router,
    admin_pricing_router,
    admin_users_router,
    auth_router,
    calibration_router,
    expert_portal_router,
    experts_router,
    fields_router,
    ingest_router,
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
    """Lifecycle hooks for startup/shutdown tasks.

    Startup:
      1. SchemaRegistry: contracts/ submodule'den şemaları yükler (KR-081)
      2. ContractValidatorService + Adapter: command handler'lara enjekte edilir
      3. app.state üzerinden paylaşılır
    Shutdown:
      - Kaynaklar temizlenir
    """
    from pathlib import Path

    from src.application.services.contract_validator_service import ContractValidatorService
    from src.infrastructure.contracts import ContractValidatorAdapter, SchemaRegistry

    import structlog

    logger = structlog.get_logger("lifespan")

    # --- KR-081: Schema yükleme ---
    registry = SchemaRegistry()
    contracts_base = Path(__file__).resolve().parents[3] / "contracts"

    if contracts_base.exists():
        schemas_dir = contracts_base / "schemas"
        enums_dir = contracts_base / "enums"
        total = 0
        if schemas_dir.exists():
            total += registry.load_directory(schemas_dir, recursive=True)
        if enums_dir.exists():
            total += registry.load_directory(enums_dir, recursive=True)
        logger.info("contracts_loaded", total=total, schemas=registry.list_schemas()[:5])
    else:
        logger.warning("contracts_submodule_missing", path=str(contracts_base))

    # --- Contract validator wiring ---
    validator_service = ContractValidatorService(registry)
    validator_adapter = ContractValidatorAdapter(validator_service)

    _app.state.schema_registry = registry
    _app.state.contract_validator_service = validator_service
    _app.state.contract_validator = validator_adapter

    # --- Service container ---
    from src.presentation.api.service_factory import create_service_container

    service_container = await create_service_container()
    _app.state.services = service_container

    # --- Database & Redis startup ---
    from src.infrastructure.persistence.database import get_engine, dispose_engine
    from src.infrastructure.persistence.redis.cache import get_redis_client, close_redis

    await get_engine()
    logger.info("database_engine_created")

    await get_redis_client()
    logger.info("redis_client_created")

    logger.info("lifespan_started", schemas_registered=len(registry.list_schemas()))

    yield

    # --- Shutdown ---
    await dispose_engine()
    await close_redis()
    registry.clear()
    logger.info("lifespan_shutdown")


async def _corr_id_middleware(request: Request, call_next: Callable[..., Any]) -> Response:
    corr_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
    request.state.corr_id = corr_id
    response: Response = await call_next(request)
    response.headers["X-Correlation-Id"] = corr_id
    return response


async def _security_headers_middleware(request: Request, call_next: Callable[..., Any]) -> Response:
    """SEC: Add security headers to all API responses (XSS, clickjacking, MIME-sniffing)."""
    response: Response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")
    response.headers.setdefault("Cache-Control", "no-store")
    # X-XSS-Protection: 0 — Modern browsers deprecated the XSS auditor;
    # setting 1 can introduce vulnerabilities. CSP is the replacement.
    response.headers.setdefault("X-XSS-Protection", "0")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(self)")
    return response


def _register_exception_handlers(app: FastAPI) -> None:
    # SEC: corr_id is logged server-side but NEVER returned in response body.
    # Leaking internal correlation IDs helps attackers correlate requests
    # and map internal infrastructure.

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, _: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": "Validation failed"},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        safe_detail = exc.detail if exc.status_code < 500 else "Internal server error"
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": safe_detail},
        )

    @app.exception_handler(Exception)
    async def handle_uncaught_exception(request: Request, exc: Exception) -> JSONResponse:
        import structlog as _sl

        _sl.get_logger("unhandled_exception").error(
            "unhandled_exception",
            exc_type=type(exc).__name__,
            exc_msg=str(exc),
            path=request.url.path,
            method=request.method,
            corr_id=getattr(request.state, "corr_id", None),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
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

    # Middleware stack — Starlette LIFO: last added = outermost (first to run).
    # Execution order (outermost → innermost):
    # 1. Correlation ID → 2. CORS → 3. Rate Limiting → 4. mTLS →
    # 5. JWT → 6. RBAC → 7. Anomaly → 8. PII Filter → 9. Grid Anonymizer →
    # 10. Security Headers
    #
    # IMPORTANT: Code order is REVERSED because add_middleware wraps the app,
    # so innermost middleware must be added FIRST, outermost LAST.
    app.middleware("http")(_security_headers_middleware)  # 10. innermost: security response headers
    app.add_middleware(GridAnonymizerMiddleware)  # 9.
    app.add_middleware(PIIFilterMiddleware)  # 8.
    app.add_middleware(AnomalyDetectionMiddleware)  # 7.
    app.add_middleware(RBACMiddleware)  # 6.
    app.add_middleware(JwtMiddleware)  # 5.
    app.add_middleware(MTLSVerifierMiddleware)  # 4.
    app.add_middleware(RateLimitMiddleware)  # 3. rate limit before auth
    add_cors_middleware(app)  # 2. CORS must be outermost
    app.middleware("http")(_corr_id_middleware)  # 1. correlation ID outermost

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Liveness probe — external callers get minimal 'ok' only.

        [H-2][FIX-6] Never reveal infrastructure state to external callers.
        Body is always {"status":"ok"} with HTTP 200. Degraded state is
        logged server-side for internal monitoring / alerting.
        """
        import logging

        _log = logging.getLogger("tarlaanaliz.health")
        components_down: list[str] = []
        try:
            from src.infrastructure.persistence.database import get_engine

            engine = await get_engine()
            from sqlalchemy import text as sa_text

            async with engine.connect() as conn:
                await conn.execute(sa_text("SELECT 1"))
        except Exception:
            components_down.append("database")
        try:
            from src.infrastructure.persistence.redis.cache import get_redis_client

            redis_client = await get_redis_client()
            await redis_client.ping()  # type: ignore[misc,unused-ignore]
        except Exception:
            components_down.append("redis")

        if components_down:
            _log.warning("health-degraded: %s unreachable", ", ".join(components_down))

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
    app.include_router(admin_dashboard_router, prefix="/api/v1")
    app.include_router(admin_pricing_router, prefix="/api/v1")
    app.include_router(admin_users_router, prefix="/api/v1")
    app.include_router(pilots_router, prefix="/api/v1")
    app.include_router(pricing_router, prefix="/api/v1")
    app.include_router(results_router, prefix="/api/v1")
    app.include_router(subscriptions_router, prefix="/api/v1")
    app.include_router(training_feedback_router, prefix="/api/v1")
    app.include_router(weather_block_reports_router, prefix="/api/v1")
    app.include_router(weather_blocks_router, prefix="/api/v1")
    app.include_router(ingest_router, prefix="/api/v1")

    _register_exception_handlers(app)
    return app


app = create_app()

__all__ = ["app", "create_app"]
