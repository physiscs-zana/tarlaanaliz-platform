# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Dataset entity v1.2.0 testleri: available_bands kontrolu."""

from __future__ import annotations

import uuid

import pytest

from src.core.domain.entities.dataset import Dataset, DatasetTransitionError
from src.core.domain.value_objects.dataset_status import DatasetStatus


def test_dataset_create_with_bands() -> None:
    """available_bands create() ile set edilmeli."""
    ds = Dataset.create(
        mission_id=uuid.uuid4(),
        field_id=uuid.uuid4(),
        available_bands=("green", "red", "red_edge", "nir"),
    )
    assert ds.available_bands == ("green", "red", "red_edge", "nir")
    assert ds.status == DatasetStatus.RAW_INGESTED


def test_dataset_create_without_bands() -> None:
    """available_bands olmadan da create edilebilir (backward-compatible)."""
    ds = Dataset.create(
        mission_id=uuid.uuid4(),
        field_id=uuid.uuid4(),
    )
    assert ds.available_bands == ()


def test_dataset_transition_calibrated_requires_bands() -> None:
    """CALIBRATED gecisi icin available_bands en az 4 band icermelidir."""
    ds = Dataset.create(
        mission_id=uuid.uuid4(),
        field_id=uuid.uuid4(),
        available_bands=(),
    )
    # RAW_INGESTED -> RAW_SCANNED_EDGE_OK
    ds.transition_to(DatasetStatus.RAW_SCANNED_EDGE_OK, av1_report_uri="s3://av1/report")
    # RAW_SCANNED_EDGE_OK -> RAW_HASH_SEALED
    ds.transition_to(DatasetStatus.RAW_HASH_SEALED, sha256_hash="abc123")
    # RAW_HASH_SEALED -> CALIBRATED (should fail: no bands)
    with pytest.raises(DatasetTransitionError, match="available_bands"):
        ds.transition_to(DatasetStatus.CALIBRATED)


def test_dataset_transition_calibrated_succeeds_with_bands() -> None:
    """available_bands 4+ band ile CALIBRATED gecisi basarili olmali."""
    ds = Dataset.create(
        mission_id=uuid.uuid4(),
        field_id=uuid.uuid4(),
        available_bands=("green", "red", "red_edge", "nir"),
    )
    ds.transition_to(DatasetStatus.RAW_SCANNED_EDGE_OK, av1_report_uri="s3://av1/report")
    ds.transition_to(DatasetStatus.RAW_HASH_SEALED, sha256_hash="abc123")
    ds.transition_to(DatasetStatus.CALIBRATED)
    assert ds.status == DatasetStatus.CALIBRATED
    assert ds.is_calibrated


def test_dataset_is_ready_for_analysis_requires_bands() -> None:
    """is_ready_for_analysis: available_bands 4+ band gerekli."""
    ds = Dataset.create(
        mission_id=uuid.uuid4(),
        field_id=uuid.uuid4(),
        available_bands=("green", "red", "red_edge", "nir"),
    )
    ds.transition_to(DatasetStatus.RAW_SCANNED_EDGE_OK, av1_report_uri="s3://av1/report")
    ds.transition_to(DatasetStatus.RAW_HASH_SEALED, sha256_hash="abc123")
    ds.transition_to(DatasetStatus.CALIBRATED)
    ds.transition_to(DatasetStatus.CALIBRATED_SCANNED_CENTER_OK, av2_report_uri="s3://av2/report")
    assert ds.is_ready_for_analysis


def test_dataset_not_ready_without_bands() -> None:
    """is_ready_for_analysis: available_bands bos ise False."""
    ds = Dataset.create(
        mission_id=uuid.uuid4(),
        field_id=uuid.uuid4(),
        available_bands=(),
    )
    # Direct state set (test shortcut)
    ds.status = DatasetStatus.CALIBRATED_SCANNED_CENTER_OK
    ds.is_calibrated = True
    ds.sha256_hash = "abc123"
    ds.av1_report_uri = "s3://av1"
    ds.av2_report_uri = "s3://av2"
    assert not ds.is_ready_for_analysis
