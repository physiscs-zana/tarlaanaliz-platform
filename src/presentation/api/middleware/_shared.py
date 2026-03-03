# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
# KR-081: Ortak middleware primitifleri; corr_id, IP maskeleme, metrik hook.
"""Shared middleware primitives for context and safe observability."""

from __future__ import annotations

import ipaddress
import logging
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


def get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return ""


def is_bypassed_path(path: str, bypass_routes: list[str]) -> bool:
    return any(path == route or path.startswith(f"{route.rstrip('/')}/") for route in bypass_routes)
