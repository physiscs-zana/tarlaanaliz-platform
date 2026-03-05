# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: SQL injection ve anomali pattern tespiti (SDLC gate).

"""SQL injection / anomaly pattern detector."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class QueryScanResult:
    is_suspicious: bool
    reason: str | None = None


class QueryPatternAnalyzer:
    """Detect obvious malicious query fragments."""

    _SUSPICIOUS_PATTERNS = (
        re.compile(r"(?i)\bunion\s+select\b"),
        re.compile(r"(?i)\bdrop\s+table\b"),
        re.compile(r"(?i)--"),
        re.compile(r"(?i)\bor\s+1\s*=\s*1\b"),
    )

    def scan(self, query: str) -> QueryScanResult:
        normalized = query.strip()
        if not normalized:
            return QueryScanResult(is_suspicious=False)

        for pattern in self._SUSPICIOUS_PATTERNS:
            if pattern.search(normalized):
                return QueryScanResult(is_suspicious=True, reason=f"pattern:{pattern.pattern}")
        return QueryScanResult(is_suspicious=False)
