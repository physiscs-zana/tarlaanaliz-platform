# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015-5: WeatherBlockReport repository SQLAlchemy implementasyonu.
"""WeatherBlockReportRepository SQLAlchemy implementation."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.weather_block_report import WeatherBlockReport
from src.core.ports.repositories.weather_block_report_repository import (
    WeatherBlockReportRepository,
)
from src.infrastructure.persistence.sqlalchemy.models.weather_block_model import (
    WeatherBlockReportModel,
)


def _model_to_entity(m: WeatherBlockReportModel) -> WeatherBlockReport:
    """ORM model → domain entity mapping."""
    return WeatherBlockReport(
        weather_block_id=m.weather_block_report_id,
        mission_id=m.mission_id,
        field_id=uuid.UUID(int=0),  # weather_block_reports'ta field_id yok; mission üzerinden elde edilir
        reported_at=m.reported_at,
        reason=m.weather_condition,
        created_at=m.created_at,
        notes=m.notes,
        resolved=m.status in ("RESOLVED", "REJECTED"),
    )


def _entity_to_model(e: WeatherBlockReport) -> WeatherBlockReportModel:
    """Domain entity → ORM model mapping."""
    model = WeatherBlockReportModel()
    model.weather_block_report_id = e.weather_block_id
    model.mission_id = e.mission_id
    model.reported_at = e.reported_at
    model.weather_condition = e.reason
    model.notes = e.notes
    model.status = "RESOLVED" if e.resolved else "REPORTED"
    return model


class WeatherBlockReportRepositoryImpl(WeatherBlockReportRepository):
    """WeatherBlockReportRepository portunun SQLAlchemy implementasyonu (KR-015-5)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, report: WeatherBlockReport) -> None:
        existing = await self._session.get(WeatherBlockReportModel, report.weather_block_id)
        if existing is not None:
            existing.weather_condition = report.reason
            existing.notes = report.notes
            existing.status = "RESOLVED" if report.resolved else "REPORTED"
        else:
            self._session.add(_entity_to_model(report))
        await self._session.flush()

    async def find_by_id(self, weather_block_id: uuid.UUID) -> Optional[WeatherBlockReport]:
        model = await self._session.get(WeatherBlockReportModel, weather_block_id)
        if model is None:
            return None
        return _model_to_entity(model)

    async def list_by_mission_id(self, mission_id: uuid.UUID) -> List[WeatherBlockReport]:
        stmt = select(WeatherBlockReportModel).where(WeatherBlockReportModel.mission_id == mission_id)
        result = await self._session.execute(stmt)
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def list_by_field_id(self, field_id: uuid.UUID) -> List[WeatherBlockReport]:
        from src.infrastructure.persistence.sqlalchemy.models.mission_model import MissionModel

        stmt = (
            select(WeatherBlockReportModel)
            .join(MissionModel, WeatherBlockReportModel.mission_id == MissionModel.mission_id)
            .where(MissionModel.field_id == field_id)
        )
        result = await self._session.execute(stmt)
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def list_unresolved_by_mission_id(self, mission_id: uuid.UUID) -> List[WeatherBlockReport]:
        stmt = select(WeatherBlockReportModel).where(
            WeatherBlockReportModel.mission_id == mission_id,
            WeatherBlockReportModel.status.in_(["REPORTED", "VERIFIED"]),
        )
        result = await self._session.execute(stmt)
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def delete(self, weather_block_id: uuid.UUID) -> None:
        model = await self._session.get(WeatherBlockReportModel, weather_block_id)
        if model is None:
            raise KeyError(f"WeatherBlockReport not found: {weather_block_id}")
        await self._session.delete(model)
        await self._session.flush()
