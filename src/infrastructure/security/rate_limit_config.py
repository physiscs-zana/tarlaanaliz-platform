# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
# KR-041: Rate-limit konfigürasyon sözleşmesi (SDLC gate).

"""Rate-limit contract parser."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitRule:
    path: str
    requests: int
    window_seconds: int


def parse_rate_limit_rules(raw_rules: list[str]) -> list[RateLimitRule]:
    """Parse rules with format: /path=requests/window_seconds."""
    rules: list[RateLimitRule] = []
    for raw_rule in raw_rules:
        path_raw, limit_raw = raw_rule.split("=", maxsplit=1)
        requests_raw, window_raw = limit_raw.split("/", maxsplit=1)
        rule = RateLimitRule(
            path=path_raw.strip(),
            requests=int(requests_raw.strip()),
            window_seconds=int(window_raw.strip()),
        )
        if not rule.path.startswith("/"):
            raise ValueError("Rate limit path must start with '/'")
        if rule.requests <= 0 or rule.window_seconds <= 0:
            raise ValueError("Rate limit values must be positive")
        rules.append(rule)
    return rules
