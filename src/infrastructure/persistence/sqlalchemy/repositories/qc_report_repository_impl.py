# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-018: QCReportRepository SQLAlchemy implementation.
"""QCReportRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.qc_report_record import QCRecommendedAction, QCReportRecord, QCStatus
from src.core.ports.repositories.qc_report_repository import QCReportRepository
from src.infrastructure.persistence.sqlalchemy.models.qc_report_model import QCReportModel


class QCReportRepositoryImpl(QCReportRepository):
    """QCReportRepository portunun async SQLAlchemy implementasyonu (KR-018, KR-082)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _to_entity(self, model: QCReportModel) -> QCReportRecord:
        """ORM modelini domain entity'sine donusturur."""
        return QCReportRecord(
            qc_report_id=model.qc_report_id,
            calibration_record_id=model.calibration_record_id,
            status=QCStatus(model.status),
            recommended_action=QCRecommendedAction(model.recommended_action),
            created_at=model.created_at,
            flags=model.flags,
            notes=model.notes,
        )

    def _apply_to_model(self, model: QCReportModel, entity: QCReportRecord) -> None:
        """Entity alanlarini ORM modeline yazar."""
        model.qc_report_id = entity.qc_report_id
        model.calibration_record_id = entity.calibration_record_id
        model.status = entity.status.value
        model.recommended_action = entity.recommended_action.value
        model.created_at = entity.created_at
        model.flags = entity.flags
        model.notes = entity.notes

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------

    async def save(self, report: QCReportRecord) -> None:
        """QCReportRecord kaydet (insert veya update)."""
        existing = await self._session.get(QCReportModel, report.qc_report_id)
        if existing:
            existing.status = report.status.value
            existing.recommended_action = report.recommended_action.value
            existing.flags = report.flags
            existing.notes = report.notes
        else:
            model = QCReportModel()
            self._apply_to_model(model, report)
            self._session.add(model)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------

    async def find_by_id(self, qc_report_id: uuid.UUID) -> Optional[QCReportRecord]:
        """qc_report_id ile QCReportRecord getir."""
        model = await self._session.get(QCReportModel, qc_report_id)
        return self._to_entity(model) if model else None

    async def find_by_calibration_record_id(self, calibration_record_id: uuid.UUID) -> Optional[QCReportRecord]:
        """calibration_record_id ile QCReportRecord getir (KR-018 hard gate)."""
        result = await self._session.execute(
            select(QCReportModel).where(QCReportModel.calibration_record_id == calibration_record_id)
        )
        model = result.scalars().first()
        return self._to_entity(model) if model else None

    # ------------------------------------------------------------------
    # Liste sorgulari
    # ------------------------------------------------------------------

    async def list_by_status(self, status: QCStatus) -> List[QCReportRecord]:
        """Belirli durumdaki tum QC raporlarini getir."""
        result = await self._session.execute(
            select(QCReportModel)
            .where(QCReportModel.status == status.value)
            .order_by(QCReportModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------

    async def delete(self, qc_report_id: uuid.UUID) -> None:
        """QCReportRecord sil."""
        await self._session.execute(
            sa_delete(QCReportModel).where(QCReportModel.qc_report_id == qc_report_id)
        )
        await self._session.flush()
