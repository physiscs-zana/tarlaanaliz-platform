# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""AnalysisResult entity v1.2.0 testleri: report_tier, thermal_summary, available_layers."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from src.core.domain.entities.analysis_result import AnalysisResult


def _result(**kwargs) -> AnalysisResult:
    defaults = dict(
        result_id=uuid.uuid4(),
        analysis_job_id=uuid.uuid4(),
        mission_id=uuid.uuid4(),
        field_id=uuid.uuid4(),
        overall_health_index=Decimal("0.75"),
        findings={"layers": ["HEALTH", "DISEASE"]},
        summary="YZ analizidir; ilaclama karari vermez.",
        created_at=datetime(2026, 3, 1),
    )
    defaults.update(kwargs)
    return AnalysisResult(**defaults)


def test_report_tier_default_temel() -> None:
    r = _result()
    assert r.report_tier == "TEMEL"


def test_report_tier_custom() -> None:
    r = _result(report_tier="KAPSAMLI")
    assert r.report_tier == "KAPSAMLI"


def test_thermal_summary_none_by_default() -> None:
    r = _result()
    assert r.thermal_summary is None


def test_thermal_summary_set() -> None:
    thermal = {"cwsi": 0.6, "canopy_temp": 32.5, "delta_t": 4.2, "irrigation_efficiency": 0.7}
    r = _result(thermal_summary=thermal)
    assert r.thermal_summary is not None
    assert r.thermal_summary["cwsi"] == 0.6


def test_available_layers_default_empty() -> None:
    r = _result()
    assert r.available_layers == ()


def test_available_layers_set() -> None:
    r = _result(available_layers=("HEALTH", "DISEASE", "THERMAL_STRESS"))
    assert len(r.available_layers) == 3
    assert "THERMAL_STRESS" in r.available_layers


def test_band_class_default_empty() -> None:
    r = _result()
    assert r.band_class == ""


def test_band_class_set() -> None:
    r = _result(band_class="EXTENDED_5BAND")
    assert r.band_class == "EXTENDED_5BAND"
