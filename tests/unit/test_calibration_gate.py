# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
KR-018 hard gate testleri.
v1.2.0: available_bands zorunlu; kalibrasyon + band kontrolu.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from src.core.domain.entities.analysis_job import AnalysisJob, AnalysisJobStatus


def _job(**kwargs) -> AnalysisJob:
    defaults = dict(
        analysis_job_id=uuid.uuid4(),
        mission_id=uuid.uuid4(),
        field_id=uuid.uuid4(),
        crop_type="WHEAT",
        analysis_type="MULTISPECTRAL",
        model_id="model-1",
        model_version="1.0.0",
        status=AnalysisJobStatus.PENDING,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
    defaults.update(kwargs)
    return AnalysisJob(**defaults)


def test_kr018_start_fails_without_calibration() -> None:
    with pytest.raises(ValueError, match="KR-018"):
        _job().start_processing()


def test_kr018_start_succeeds_with_calibration() -> None:
    job = _job(available_bands=("green", "red", "red_edge", "nir"))
    job.attach_calibration(uuid.uuid4())
    job.start_processing()
    assert job.status == AnalysisJobStatus.PROCESSING


# ---- v1.2.0: available_bands kontrolu ----

def test_kr018_v120_start_fails_without_available_bands() -> None:
    """KR-018 v1.2.0: available_bands bos ise start_processing basarisiz olmali."""
    job = _job(available_bands=())
    job.attach_calibration(uuid.uuid4())
    with pytest.raises(ValueError, match="available_bands"):
        job.start_processing()


def test_kr018_v120_start_succeeds_with_available_bands() -> None:
    """KR-018 v1.2.0: available_bands 4+ band ile start_processing basarili olmali."""
    job = _job(available_bands=("green", "red", "red_edge", "nir"))
    job.attach_calibration(uuid.uuid4())
    job.start_processing()
    assert job.status == AnalysisJobStatus.PROCESSING


def test_kr018_v120_start_succeeds_with_5band() -> None:
    """5-band ile de basarili olmali (Graceful Degradation)."""
    job = _job(available_bands=("blue", "green", "red", "red_edge", "nir"))
    job.attach_calibration(uuid.uuid4())
    job.start_processing()
    assert job.status == AnalysisJobStatus.PROCESSING


def test_kr018_v120_start_succeeds_with_thermal() -> None:
    """5-band + termal ile de basarili olmali."""
    job = _job(available_bands=("blue", "green", "red", "red_edge", "nir", "thermal"))
    job.attach_calibration(uuid.uuid4())
    job.start_processing()
    assert job.status == AnalysisJobStatus.PROCESSING
