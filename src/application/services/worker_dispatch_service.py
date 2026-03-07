# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-070: Worker full isolation - inbound HTTP forbidden; queue consume-only.
# KR-072: Dataset CALIBRATED_SCANNED_CENTER_OK -> DISPATCHED_TO_WORKER transition.
# KR-018: Calibration hard gate.
"""Worker dispatch service: dispatches dataset to worker queue."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

import structlog

logger = structlog.get_logger(__name__)


class EventBusPort(Protocol):
    async def publish(self, event: Any) -> None: ...


class DatasetRepositoryPort(Protocol):
    async def get_by_id(self, dataset_id: uuid.UUID) -> Any: ...
    async def save(self, dataset: Any) -> None: ...


class AnalysisJobRepositoryPort(Protocol):
    async def save(self, job: Any) -> None: ...


@dataclass(frozen=True, slots=True)
class DispatchResult:
    dataset_id: str
    analysis_job_id: str
    status: str
    dispatched_at: str


class WorkerDispatchService:
    """Dispatches dataset to worker queue for analysis (KR-070, KR-072).

    Flow:
    1. Verify dataset is in CALIBRATED_SCANNED_CENTER_OK state
    2. Check is_ready_for_analysis (calibration, AV reports, hash)
    3. Create AnalysisJob
    4. Transition dataset to DISPATCHED_TO_WORKER state
    5. Publish AnalysisRequested event (worker will consume)
    """

    def __init__(
        self,
        *,
        dataset_repo: DatasetRepositoryPort,
        job_repo: AnalysisJobRepositoryPort,
        event_bus: EventBusPort,
    ) -> None:
        self._dataset_repo = dataset_repo
        self._job_repo = job_repo
        self._event_bus = event_bus

    async def dispatch_to_worker(
        self,
        *,
        dataset_id: uuid.UUID,
        crop_type: str,
        analysis_type: str = "standard",
        model_id: str = "default",
        model_version: str = "1.0",
        correlation_id: str = "",
    ) -> DispatchResult:
        """Dispatch dataset to worker queue.

        Args:
            dataset_id: Dataset to dispatch.
            crop_type: Crop type (analysis parameter).
            analysis_type: Analysis type (standard, detailed).
            model_id: AI model identifier.
            model_version: Model version.
            correlation_id: Tracing ID.

        Returns:
            DispatchResult: Dispatch result.

        Raises:
            ValueError: If dataset is not ready for analysis.
            RuntimeError: If dataset is not found.
        """
        from src.core.domain.entities.analysis_job import AnalysisJob, AnalysisJobStatus
        from src.core.domain.events.analysis_events import AnalysisRequested
        from src.core.domain.value_objects.dataset_status import DatasetStatus

        dataset = await self._dataset_repo.get_by_id(dataset_id)
        if dataset is None:
            raise RuntimeError(f"Dataset not found: {dataset_id}")

        if not dataset.is_ready_for_analysis:
            raise ValueError(
                f"Dataset not ready for analysis. "
                f"Status: {dataset.status}, "
                f"Calibration: {dataset.is_calibrated}, "
                f"AV1: {dataset.av1_report_uri is not None}, "
                f"AV2: {dataset.av2_report_uri is not None}, "
                f"Bands: {len(dataset.available_bands)}"
            )

        # Create AnalysisJob
        job_id = uuid.uuid4()
        band_count = len(dataset.available_bands)
        band_class = "EXTENDED_5BAND" if band_count >= 5 else "BASIC_4BAND"

        job = AnalysisJob(
            analysis_job_id=job_id,
            mission_id=dataset.mission_id,
            field_id=dataset.field_id,
            crop_type=crop_type,
            analysis_type=analysis_type,
            model_id=model_id,
            model_version=model_version,
            requires_calibrated=True,
            calibration_record_id=uuid.uuid4(),
            available_bands=dataset.available_bands,
            band_class=band_class,
            status=AnalysisJobStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await self._job_repo.save(job)

        # Update dataset status
        dataset.transition_to(
            DatasetStatus.DISPATCHED_TO_WORKER,
            worker_job_id=job_id,
            manifest_update={"dispatched_at": datetime.now(UTC).isoformat()},
        )
        await self._dataset_repo.save(dataset)

        # Publish event - worker will consume this event
        event = AnalysisRequested(
            mission_id=dataset.mission_id,
            field_id=dataset.field_id,
            crop_type=crop_type,
            requires_calibrated=True,
            available_bands=dataset.available_bands,
        )
        await self._event_bus.publish(event)

        logger.info(
            "worker_dispatch_completed",
            dataset_id=str(dataset_id),
            analysis_job_id=str(job_id),
            band_class=band_class,
            correlation_id=correlation_id,
        )

        return DispatchResult(
            dataset_id=str(dataset_id),
            analysis_job_id=str(job_id),
            status="DISPATCHED_TO_WORKER",
            dispatched_at=datetime.now(UTC).isoformat(),
        )
