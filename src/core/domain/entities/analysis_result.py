# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/entities/analysis_result.py
# DESC: AnalysisResult; metadata + layer referanslari.
# SSOT: KR-081 (contract-first JSON Schema), KR-025 (analiz icerigi)
"""
AnalysisResult domain entity.

YZ analiz sonucu: overall_health_index + findings + summary.
YZ analizidir; ilaclama karari VERMEZ (KR-001, KR-025).
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Union

# KR-025: Blocked keywords — system must NEVER produce pesticide/herbicide/
# fungicide recommendations. This regex catches Turkish and English terms.
_KR025_BLOCKED_PATTERN = re.compile(
    r"\b("
    r"pesticide|pestisit|herbicide|herbisit|fungicide|fungisit|insecticide|insektisit"
    r"|ilaclama|ilac[_\s]?onerisi|sprey|spreyleme|puskurtme"
    r"|gubreleme|fertiliz|fertilization"
    r"|doz[_\s]?oner|uygulama[_\s]?kara|application[_\s]?decision"
    r"|prescription|recete"
    r")\b",
    re.IGNORECASE,
)


@dataclass
class AnalysisResult:
    """Analiz sonucu domain entity'si.

    * KR-081   -- Contract-first AnalysisResult JSON Schema.
    * KR-025   -- Rapor ciktisi: health score, su/azot stresi, hastalik, zararli, yabanci ot.
    * KR-001   -- YZ sadece analiz yapar; ilaclama/gubreleme karari VERMEZ.
    * KR-023 v1.2.0 -- Katmanli rapor: TEMEL / GENISLETILMIS / KAPSAMLI.
    * KR-084 v1.2.0 -- Termal analiz sonuclari (opsiyonel).

    summary alani: 'YZ analizidir; ilaclama karari vermez.' uyarisini icerir.

    KR-025 RUNTIME ENFORCEMENT: __post_init__ rejects any content containing
    pesticide/herbicide/fungicide recommendation keywords in summary or findings.
    """

    result_id: uuid.UUID
    analysis_job_id: uuid.UUID
    mission_id: uuid.UUID
    field_id: uuid.UUID
    overall_health_index: Decimal  # 0-1
    findings: Union[Dict[str, Any], List[Any]]  # JSONB
    summary: str  # YZ analizidir, ilaclama karari vermez
    created_at: datetime
    # KR-023 v1.2.0: Katmanli rapor + Graceful Degradation
    report_tier: str = "TEMEL"  # TEMEL | GENISLETILMIS | KAPSAMLI
    band_class: str = ""  # BASIC_4BAND | EXTENDED_5BAND
    available_layers: tuple[str, ...] = ()  # uretilen katman kodlari
    # KR-084 v1.2.0: Termal analiz sonuclari (yalnizca LWIR/THERMAL band varsa)
    thermal_summary: Union[Dict[str, Any], None] = None  # cwsi, canopy_temp, delta_t, irrigation_efficiency

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if not (Decimal("0") <= self.overall_health_index <= Decimal("1")):
            raise ValueError(f"overall_health_index must be between 0 and 1, got {self.overall_health_index}")
        if self.findings is None:
            raise ValueError("findings is required (can be empty dict or list)")
        if not self.summary:
            raise ValueError("summary is required")
        # KR-025: Runtime enforcement — reject any pesticide/herbicide/
        # fungicide recommendation content in summary or findings
        self._enforce_kr025()

    # ------------------------------------------------------------------
    # KR-025: Blocked content enforcement
    # ------------------------------------------------------------------
    def _enforce_kr025(self) -> None:
        """KR-025: Reject content containing pesticide/herbicide/fungicide recommendations."""
        # Check summary
        if _KR025_BLOCKED_PATTERN.search(self.summary):
            raise ValueError(
                "KR-025 VIOLATION: summary contains blocked pesticide/herbicide/fungicide "
                "recommendation keywords. System must NOT make spraying/fertilization decisions."
            )
        # Check findings recursively
        self._scan_findings_for_blocked_content(self.findings, "findings")

    def _scan_findings_for_blocked_content(self, data: Any, path: str) -> None:
        """Recursively scan findings for KR-025 blocked keywords."""
        if isinstance(data, str):
            if _KR025_BLOCKED_PATTERN.search(data):
                raise ValueError(
                    f"KR-025 VIOLATION at '{path}': contains blocked pesticide/herbicide/"
                    f"fungicide recommendation keywords."
                )
        elif isinstance(data, dict):
            for key, value in data.items():
                # Block known recommendation-type keys
                lower_key = key.lower()
                if lower_key in ("recommendations", "prescription", "prescriptions",
                                 "pesticide_advice", "spray_plan", "ilaclama_plani"):
                    raise ValueError(
                        f"KR-025 VIOLATION: findings contains blocked key '{key}'. "
                        f"System must NOT include recommendation/prescription fields."
                    )
                self._scan_findings_for_blocked_content(value, f"{path}.{key}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._scan_findings_for_blocked_content(item, f"{path}[{i}]")
