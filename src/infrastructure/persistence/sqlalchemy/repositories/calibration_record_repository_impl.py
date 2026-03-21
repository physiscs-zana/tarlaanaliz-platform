# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-018: CalibrationRecordRepository SQLAlchemy implementation.
"""CalibrationRecordRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.calibration_record import CalibrationRecord, CalibrationStatus
from src.core.ports.repositories.calibration_record_repository import CalibrationRecordRepository
from src.infrastructure.persistence.sqlalchemy.models.calibration_record_model import CalibrationRecordModel


class CalibrationRecordRepositoryImpl(CalibrationRecordRepository):
    """CalibrationRecordRepository portunun async SQLAlchemy implementasyonu (KR-018, KR-082)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _to_entity(self, model: CalibrationRecordModel) -> CalibrationRecord:
        """ORM modelini domain entity'sine donusturur."""
        return CalibrationRecord(
            calibration_record_id=model.calibration_record_id,
            mission_id=model.mission_id,
            status=CalibrationStatus(model.status),
            created_at=model.created_at,
            batch_id=model.batch_id,
            calibration_manifest=model.calibration_manifest,
            processing_report_uri=model.processing_report_uri,
            calibration_result_uri=model.calibration_result_uri,
            qc_report_uri=model.qc_report_uri,
        )

    def _apply_to_model(self, model: CalibrationRecordModel, entity: CalibrationRecord) -> None:
        """Entity alanlarini ORM modeline yazar."""
        model.calibration_record_id = entity.calibration_record_id
        model.mission_id = entity.mission_id
        model.status = entity.status.value
        model.created_at = entity.created_at
        model.batch_id = entity.batch_id
        model.calibration_manifest = entity.calibration_manifest
        model.processing_report_uri = entity.processing_report_uri
        model.calibration_result_uri = entity.calibration_result_uri
        model.qc_report_uri = entity.qc_report_uri

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------

    async def save(self, record: CalibrationRecord) -> None:
        """CalibrationRecord kaydet (insert veya update)."""
        existing = await self._session.get(CalibrationRecordModel, record.calibration_record_id)
        if existing:
            existing.status = record.status.value
            existing.batch_id = record.batch_id
            existing.calibration_manifest = record.calibration_manifest
            existing.processing_report_uri = record.processing_report_uri
            existing.calibration_result_uri = record.calibration_result_uri
            existing.qc_report_uri = record.qc_report_uri
        else:
            model = CalibrationRecordModel()
            self._apply_to_model(model, record)
            self._session.add(model)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------

    async def find_by_id(self, calibration_record_id: uuid.UUID) -> Optional[CalibrationRecord]:
        """calibration_record_id ile CalibrationRecord getir."""
        model = await self._session.get(CalibrationRecordModel, calibration_record_id)
        return self._to_entity(model) if model else None

    # ------------------------------------------------------------------
    # Liste sorgulari
    # ------------------------------------------------------------------

    async def list_by_mission_id(self, mission_id: uuid.UUID) -> List[CalibrationRecord]:
        """Bir mission'a ait tum kalibrasyon kayitlarini getir."""
        result = await self._session.execute(
            select(CalibrationRecordModel)
            .where(CalibrationRecordModel.mission_id == mission_id)
            .order_by(CalibrationRecordModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_mission_id_and_status(
        self,
        mission_id: uuid.UUID,
        status: CalibrationStatus,
    ) -> Optional[CalibrationRecord]:
        """Bir mission icin belirli durumdaki kalibrasyon kaydini getir (KR-018 hard gate)."""
        result = await self._session.execute(
            select(CalibrationRecordModel)
            .where(CalibrationRecordModel.mission_id == mission_id)
            .where(CalibrationRecordModel.status == status.value)
            .order_by(CalibrationRecordModel.created_at.desc())
        )
        model = result.scalars().first()
        return self._to_entity(model) if model else None

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------

    async def delete(self, calibration_record_id: uuid.UUID) -> None:
        """CalibrationRecord sil."""
        await self._session.execute(
            sa_delete(CalibrationRecordModel).where(
                CalibrationRecordModel.calibration_record_id == calibration_record_id
            )
        )
        await self._session.flush()
