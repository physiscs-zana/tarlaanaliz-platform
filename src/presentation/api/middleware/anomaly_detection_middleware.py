# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033: audit-compatible anomaly event emission.
"""Rule-based anomaly detection middleware with safe event emission and active blocking."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.presentation.api.middleware._shared import (
    METRICS_HOOK,
    ensure_request_context,
    get_client_ip,
    is_bypassed_path,
    mask_ip,
)
from src.presentation.api.settings import settings

LOGGER = logging.getLogger("api.middleware.anomaly")

# SEC-FIX: Threshold above which requests are actively blocked (not just logged)
_BLOCK_THRESHOLD = 0.8


@dataclass(slots=True)
class AnomalyDetectedEvent:
    corr_id: str
    path: str
    status_code: int
    anomaly_score: float
    reasons: list[str]
    masked_ip: str


class AnomalyDetectionMiddleware(BaseHTTPMiddleware):
    """Detect unusual request patterns and block/emit internal observability events."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self._request_history: dict[str, deque[float]] = defaultdict(deque)
        self._error_history: dict[str, deque[float]] = defaultdict(deque)
        self._known_user_agents: set[str] = {
            "python-httpx",
            "python-requests",
            "mozilla",
            "curl",
            "postmanruntime",
        }

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        corr_id, start_time = ensure_request_context(request)

        if not settings.anomaly.enabled or is_bypassed_path(request.url.path, settings.anomaly.allowlist_routes):
            response: Response = await call_next(request)
            response.headers["X-Correlation-Id"] = corr_id
            return response

        now = time.monotonic()
        client_ip = get_client_ip(request)
        ip_key = mask_ip(client_ip)
        history = self._request_history[ip_key]
        repeat_count = self._record_and_count(history, now, settings.anomaly.rapid_repeat_window_seconds)

        # --- Pre-response anomaly scoring (can block before processing) ---
        reasons: list[str] = []
        score = 0.0

        if repeat_count >= settings.anomaly.rapid_repeat_threshold:
            reasons.append("rapid_repeat")
            score += 0.5

        content_length = self._content_length(request)
        if content_length > settings.anomaly.large_body_threshold_bytes:
            reasons.append("large_body")
            score += 0.4

        user_agent = request.headers.get("user-agent", "").lower()
        if user_agent and not any(agent in user_agent for agent in self._known_user_agents):
            reasons.append("uncommon_user_agent")
            score += 0.2

        # SEC-FIX: Block request BEFORE processing if pre-score exceeds threshold
        if score >= _BLOCK_THRESHOLD:
            METRICS_HOOK.increment("anomaly_blocked_total")
            LOGGER.warning(
                "AnomalyBlocked",
                extra={
                    "event_name": "AnomalyBlocked",
                    "corr_id": corr_id,
                    "path": request.url.path,
                    "anomaly_score": round(score, 3),
                    "reasons": reasons,
                    "masked_ip": ip_key,
                },
            )
            resp = JSONResponse(status_code=429, content={"detail": "Too Many Requests"})
            resp.headers["Retry-After"] = "60"
            resp.headers["X-Correlation-Id"] = corr_id
            return resp

        response = await call_next(request)

        latency_ms = (time.monotonic() - start_time) * 1000
        METRICS_HOOK.observe_ms("http_latency_ms", latency_ms)
        METRICS_HOOK.increment(f"http_status_total:{response.status_code}")

        # --- Post-response checks (error spike — log only) ---
        if response.status_code >= 400:
            err_history = self._error_history[ip_key]
            error_count = self._record_and_count(err_history, now, settings.anomaly.rapid_repeat_window_seconds)
            if error_count >= 4:
                reasons.append("error_spike")
                score += 0.4

        if score >= _BLOCK_THRESHOLD:
            event = AnomalyDetectedEvent(
                corr_id=corr_id,
                path=request.url.path,
                status_code=response.status_code,
                anomaly_score=round(score, 3),
                reasons=reasons,
                masked_ip=ip_key,
            )
            METRICS_HOOK.increment("anomaly_detected_total")
            LOGGER.warning(
                "AnomalyDetected",
                extra={
                    "event_name": "AnomalyDetected",
                    "corr_id": event.corr_id,
                    "path": event.path,
                    "status_code": event.status_code,
                    "anomaly_score": event.anomaly_score,
                    "reasons": event.reasons,
                    "masked_ip": event.masked_ip,
                },
            )

        response.headers["X-Correlation-Id"] = corr_id
        return response

    @staticmethod
    def _record_and_count(history: deque[float], now: float, window_seconds: int) -> int:
        window_start = now - float(window_seconds)
        while history and history[0] < window_start:
            history.popleft()
        history.append(now)
        return len(history)

    @staticmethod
    def _content_length(request: Request) -> int:
        raw = request.headers.get("content-length", "0")
        try:
            return max(0, int(raw))
        except ValueError:
            return 0
