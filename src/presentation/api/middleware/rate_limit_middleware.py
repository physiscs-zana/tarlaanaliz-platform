# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: SDLC rate limiting gate.
"""Rate limiting middleware with pluggable backend adapter and endpoint-specific limits."""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Protocol

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.presentation.api.middleware._shared import (
    METRICS_HOOK,
    ensure_request_context,
    get_client_ip,
    is_bypassed_path,
)
from src.presentation.api.settings import settings


class RateLimitStore(Protocol):
    """Adapter interface for distributed rate-limit implementations."""

    def allow(self, key: str, now: float, per_minute: int, burst: int) -> tuple[bool, int]:
        """Return if request is allowed and retry_after seconds."""


@dataclass(slots=True)
class InMemorySlidingWindowStore:
    """Process-local sliding window store."""

    lock: threading.Lock = threading.Lock()
    buckets: dict[str, deque[float]] | None = None

    def __post_init__(self) -> None:
        if self.buckets is None:
            self.buckets = {}

    def allow(self, key: str, now: float, per_minute: int, burst: int) -> tuple[bool, int]:
        limit = max(1, per_minute + burst)
        assert self.buckets is not None
        with self.lock:
            bucket = self.buckets.setdefault(key, deque())
            window_start = now - 60.0
            while bucket and bucket[0] < window_start:
                bucket.popleft()

            if len(bucket) >= limit:
                retry_after = max(1, math.ceil(60 - (now - bucket[0])))
                return False, retry_after

            bucket.append(now)
            return True, 0


# SEC-FIX: Endpoint-specific rate limits (stricter for auth endpoints)
_ENDPOINT_LIMITS: dict[str, tuple[int, int]] = {
    # path_prefix: (per_minute, burst)
    "/api/v1/auth/phone-pin/login": (5, 2),
    "/api/v1/auth/phone-pin/register": (3, 1),
    "/api/v1/auth/phone-pin/refresh": (10, 3),
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply rate limiting based on IP and authenticated user.

    SEC-FIX: Uses full IP (not masked) for rate limit keys to prevent
    subnet-sharing bypass. Masked IP used only for logging.
    """

    def __init__(self, app: Any, store: RateLimitStore | None = None) -> None:
        super().__init__(app)
        self._store = store or InMemorySlidingWindowStore()

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        corr_id, _ = ensure_request_context(request)
        if not settings.rate_limit.enabled or is_bypassed_path(request.url.path, settings.rate_limit.bypass_routes):
            response: Response = await call_next(request)
            response.headers["X-Correlation-Id"] = corr_id
            return response

        client_ip = get_client_ip(request)
        user_id = getattr(getattr(request.state, "user", None), "user_id", None) or "anonymous"
        # SEC-FIX: Use full IP for rate limit key (masked IP allows subnet bypass)
        key = f"{client_ip}:{user_id}"

        # Determine per_minute and burst — use endpoint-specific if matched
        per_minute = settings.rate_limit.per_minute_limit
        burst = settings.rate_limit.burst
        for path_prefix, (ep_pm, ep_burst) in _ENDPOINT_LIMITS.items():
            if request.url.path.startswith(path_prefix):
                per_minute = ep_pm
                burst = ep_burst
                key = f"ep:{client_ip}:{request.url.path}"
                break

        allowed, retry_after = self._store.allow(
            key=key,
            now=time.monotonic(),
            per_minute=per_minute,
            burst=burst,
        )

        if not allowed:
            METRICS_HOOK.increment("rate_limit_block_total")
            response = JSONResponse(status_code=429, content={"detail": "Too Many Requests"})
            response.headers["Retry-After"] = str(retry_after)
            response.headers["X-Correlation-Id"] = corr_id
            return response

        response = await call_next(request)
        response.headers["X-Correlation-Id"] = corr_id
        return response
