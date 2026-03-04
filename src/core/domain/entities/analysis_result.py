# PATH: src/core/domain/entities/analysis_result.py
# DESC: AnalysisResult; metadata + layer referanslari.
# SSOT: KR-081 (contract-first JSON Schema), KR-025 (analiz icerigi)
"""
AnalysisResult domain entity.

YZ analiz sonucu: overall_health_index + findings + summary.
YZ analizidir; ilaclama karari VERMEZ (KR-001, KR-025).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Union


@dataclass
class AnalysisResult:
    """Analiz sonucu domain entity'si.

    * KR-081   -- Contract-first AnalysisResult JSON Schema.
    * KR-025   -- Rapor ciktisi: health score, su/azot stresi, hastalik, zararli, yabanci ot.
    * KR-001   -- YZ sadece analiz yapar; ilaclama/gubreleme karari VERMEZ.
    * KR-023 v1.2.0 -- Katmanli rapor: TEMEL / GENISLETILMIS / KAPSAMLI.
    * KR-084 v1.2.0 -- Termal analiz sonuclari (opsiyonel).

    summary alani: 'YZ analizidir; ilaclama karari vermez.' uyarisini icerir.
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
            raise ValueError(
                f"overall_health_index must be between 0 and 1, "
                f"got {self.overall_health_index}"
            )
        if self.findings is None:
            raise ValueError("findings is required (can be empty dict or list)")
        if not self.summary:
            raise ValueError("summary is required")
