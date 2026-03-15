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
        re.compile(r"(?i)\bunion\s+(all\s+)?select\b"),
        re.compile(r"(?i)\bdrop\s+(table|database)\b"),
        re.compile(r"--"),
        re.compile(r"(?i)\bor\s+1\s*=\s*1\b"),
        re.compile(r"(?i)\bor\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?"),
        re.compile(r"(?i);\s*(delete|update|insert|drop|alter|create|truncate|exec)\b"),
        re.compile(r"(?i)\bexec\s+(xp_|sp_)\w+"),
        re.compile(r"(?i)\bwaitfor\s+delay\b"),
        re.compile(r"(?i)\bbenchmark\s*\("),
        re.compile(r"(?i)\binto\s+(out|dump)file\b"),
        re.compile(r"(?i)\bload_file\s*\("),
        re.compile(r"(?i)\bchar\s*\(\s*\d+"),
        re.compile(r"(?i)\bconvert\s*\(\s*\w+\s+using\b"),
        re.compile(r"(?i)\binformation_schema\b"),
        re.compile(r"0x[0-9a-fA-F]{8,}"),
    )

    def scan(self, query: str) -> QueryScanResult:
        normalized = query.strip()
        if not normalized:
            return QueryScanResult(is_suspicious=False)

        for pattern in self._SUSPICIOUS_PATTERNS:
            if pattern.search(normalized):
                return QueryScanResult(is_suspicious=True, reason=f"pattern:{pattern.pattern}")
        return QueryScanResult(is_suspicious=False)
