# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: Ortak middleware primitifleri; corr_id, IP maskeleme, metrik hook.
"""Shared middleware primitives for context and safe observability."""

from __future__ import annotations

import ipaddress
import logging
import os
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field

from starlette.requests import Request

LOGGER = logging.getLogger("api.middleware")


@dataclass(slots=True)
class MetricsHook:
    """Process-local metric sink to keep middleware testable."""

    counters: Counter[str] = field(default_factory=Counter)
    timings_ms: dict[str, list[float]] = field(default_factory=dict)

    def increment(self, name: str, value: int = 1) -> None:
        self.counters[name] += value

    def observe_ms(self, name: str, duration_ms: float) -> None:
        self.timings_ms.setdefault(name, []).append(duration_ms)


METRICS_HOOK = MetricsHook()


def ensure_request_context(request: Request) -> tuple[str, float]:
    corr_id = request.headers.get("X-Correlation-Id") or getattr(request.state, "corr_id", None)
    if not corr_id:
        corr_id = str(uuid.uuid4())
    request.state.corr_id = corr_id

    start_time = getattr(request.state, "start_time", None)
    if start_time is None:
        start_time = time.monotonic()
        request.state.start_time = start_time

    return corr_id, float(start_time)


def mask_ip(ip_value: str | None) -> str:
    """Mask IP for logging/audit — NEVER use for rate limiting keys."""
    if not ip_value:
        return "unknown"
    try:
        address = ipaddress.ip_address(ip_value)
    except ValueError:
        return "unknown"

    if address.version == 4:
        network = ipaddress.ip_network(f"{address}/24", strict=False)
        return str(network.network_address) + "/24"

    network_v6 = ipaddress.ip_network(f"{address}/64", strict=False)
    return str(network_v6.network_address) + "/64"


# ---------------------------------------------------------------------------
# SEC-FIX: Trusted proxy validation for X-Forwarded-For
# ---------------------------------------------------------------------------
def _get_trusted_proxies() -> set[str]:
    """Load trusted proxy CIDRs from env (comma-separated)."""
    raw = os.getenv("TRUSTED_PROXY_CIDRS", "")
    if not raw.strip():
        return {"127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "::1/128"}
    return {c.strip() for c in raw.split(",") if c.strip()}


_TRUSTED_PROXIES: set[str] | None = None


def _is_trusted_proxy(ip_str: str) -> bool:
    """Check if IP is from a trusted proxy network."""
    global _TRUSTED_PROXIES
    if _TRUSTED_PROXIES is None:
        _TRUSTED_PROXIES = _get_trusted_proxies()
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    for cidr in _TRUSTED_PROXIES:
        try:
            if addr in ipaddress.ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue
    return False


def get_client_ip(request: Request) -> str:
    """Extract real client IP with trusted proxy validation.

    SEC-FIX: Only trust X-Forwarded-For when the direct connection is from
    a known trusted proxy. Otherwise use the direct connection IP.
    """
    direct_ip = request.client.host if request.client else ""

    xff = request.headers.get("x-forwarded-for")
    if xff and _is_trusted_proxy(direct_ip):
        return xff.split(",")[0].strip()

    return direct_ip


def is_bypassed_path(path: str, bypass_routes: list[str]) -> bool:
    return any(path == route or path.startswith(f"{route.rstrip('/')}/") for route in bypass_routes)
