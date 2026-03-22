# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-063: Central RBAC middleware - role check on every request.
"""RBAC (Role-Based Access Control) middleware.

KR-063: Real authorization is enforced on the backend.
Frontend RBAC is for visualization only.

Checks allowed roles based on route prefixes.
Bypass routes (auth, health, docs) are skipped.
"""

from __future__ import annotations

from collections.abc import Callable, Awaitable

from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = structlog.get_logger(__name__)


# Route prefix -> allowed roles mapping
_ROUTE_ROLES: list[tuple[str, frozenset[str]]] = [
    # Admin endpoints
    ("/api/v1/admin/", frozenset({"CENTRAL_ADMIN", "BILLING_ADMIN"})),
    # Expert portal
    ("/api/v1/expert/", frozenset({"EXPERT", "CENTRAL_ADMIN"})),
    # Ingest (edge kiosk) - also protected by mTLS
    ("/api/v1/ingest/", frozenset({"STATION_OPERATOR", "CENTRAL_ADMIN"})),
    # Pilot
    ("/api/v1/pilots", frozenset({"PILOT", "CENTRAL_ADMIN"})),
    # Weather block
    ("/api/v1/weather-block", frozenset({"PILOT", "CENTRAL_ADMIN"})),
    # QC + Calibration
    ("/api/v1/qc/", frozenset({"STATION_OPERATOR", "CENTRAL_ADMIN"})),
    ("/api/v1/calibration/", frozenset({"STATION_OPERATOR", "CENTRAL_ADMIN"})),
    # Training feedback
    ("/api/v1/training-feedback/", frozenset({"AI_SERVICE", "EXPERT", "CENTRAL_ADMIN"})),
    # Fields
    (
        "/api/v1/fields",
        frozenset(
            {
                "FARMER_SINGLE",
                "FARMER_MEMBER",
                "COOP_OWNER",
                "COOP_ADMIN",
                "COOP_AGRONOMIST",
                "CENTRAL_ADMIN",
            }
        ),
    ),
    # Missions
    (
        "/api/v1/missions",
        frozenset(
            {
                "FARMER_SINGLE",
                "FARMER_MEMBER",
                "COOP_OWNER",
                "COOP_ADMIN",
                "PILOT",
                "CENTRAL_ADMIN",
            }
        ),
    ),
    # Payments
    (
        "/api/v1/payments",
        frozenset(
            {
                "FARMER_SINGLE",
                "FARMER_MEMBER",
                "COOP_OWNER",
                "BILLING_ADMIN",
                "CENTRAL_ADMIN",
            }
        ),
    ),
    # Subscriptions
    (
        "/api/v1/subscriptions",
        frozenset(
            {
                "FARMER_SINGLE",
                "FARMER_MEMBER",
                "COOP_OWNER",
                "COOP_ADMIN",
                "CENTRAL_ADMIN",
            }
        ),
    ),
    # Results
    (
        "/api/v1/results",
        frozenset(
            {
                "FARMER_SINGLE",
                "FARMER_MEMBER",
                "COOP_OWNER",
                "COOP_ADMIN",
                "COOP_AGRONOMIST",
                "EXPERT",
                "CENTRAL_ADMIN",
            }
        ),
    ),
    # Parcels
    (
        "/api/v1/parcels",
        frozenset(
            {
                "FARMER_SINGLE",
                "FARMER_MEMBER",
                "COOP_OWNER",
                "COOP_ADMIN",
                "COOP_AGRONOMIST",
                "CENTRAL_ADMIN",
            }
        ),
    ),
    # Cooperatives management (KR-014)
    (
        "/api/v1/cooperatives",
        frozenset(
            {
                "FARMER_SINGLE",
                "FARMER_MEMBER",
                "COOP_OWNER",
                "COOP_ADMIN",
                "COOP_AGRONOMIST",
                "COOP_VIEWER",
                "CENTRAL_ADMIN",
            }
        ),
    ),
    # Cooperative member/invite operations (KR-014)
    (
        "/api/v1/coop/",
        frozenset(
            {
                "FARMER_SINGLE",
                "FARMER_MEMBER",
                "COOP_OWNER",
                "COOP_ADMIN",
                "COOP_AGRONOMIST",
                "COOP_VIEWER",
                "CENTRAL_ADMIN",
            }
        ),
    ),
    # SLA metrics - IL_OPERATOR KPI access (KR-083: PII-free KPI + capacity metrics)
    (
        "/api/v1/sla-metrics",
        frozenset({"IL_OPERATOR", "CENTRAL_ADMIN"}),
    ),
    # Expert management (admin-only CRUD)
    ("/api/v1/experts", frozenset({"CENTRAL_ADMIN"})),
    # Weather block reports
    ("/api/v1/weather-block-reports", frozenset({"PILOT", "CENTRAL_ADMIN"})),
    # Expert portal (expert reviews)
    ("/api/v1/expert-portal", frozenset({"EXPERT", "CENTRAL_ADMIN"})),
]

_BYPASS_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/",
    "/api/v1/pricing",  # public read-only
    "/api/v1/layers",  # public read-only — KR-002 layer registry
    "/api/v1/payments/methods",  # public — payment methods info
)


class RBACMiddleware(BaseHTTPMiddleware):
    """Central role-based access control (KR-063).

    Runs after JWT middleware.
    Compares request.state.roles list against _ROUTE_ROLES.
    Returns 403 Forbidden if no match.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        path = request.url.path

        # Bypass check
        for prefix in _BYPASS_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # OPTIONS preflight bypass
        if request.method == "OPTIONS":
            return await call_next(request)

        # SEC-FIX: Default-deny — unauthenticated requests are rejected (was default-open)
        user = getattr(request.state, "user", None)
        if user is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"},
            )

        # User roles
        user_roles = set(getattr(request.state, "roles", []))

        # Find route match
        for route_prefix, allowed_roles in _ROUTE_ROLES:
            if path.startswith(route_prefix):
                if not user_roles.intersection(allowed_roles):
                    corr_id = getattr(request.state, "corr_id", "")
                    logger.warning(
                        "rbac_denied",
                        path=path,
                        user_roles=sorted(user_roles),
                        required_roles=sorted(allowed_roles),
                        corr_id=corr_id,
                    )
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Forbidden"},
                    )
                break  # Match found, access granted
        else:
            # SEC-FIX: Default-deny — no route matched, reject /api/ requests
            if path.startswith("/api/"):
                corr_id = getattr(request.state, "corr_id", "")
                logger.warning(
                    "rbac_denied_no_route_match",
                    path=path,
                    user_roles=sorted(user_roles),
                    corr_id=corr_id,
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Forbidden"},
                )

        return await call_next(request)
