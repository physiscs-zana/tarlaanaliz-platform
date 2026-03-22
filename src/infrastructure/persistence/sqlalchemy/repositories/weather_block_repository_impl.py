# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015-5: WeatherBlock repository SQLAlchemy implementasyonu.
"""WeatherBlockRepository SQLAlchemy implementation."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.weather_block_report import WeatherBlockReport
from src.core.domain.value_objects.weather_block_status import WeatherBlockStatus
from src.core.ports.repositories.weather_block_repository import WeatherBlockRepository
from src.infrastructure.persistence.sqlalchemy.models.weather_block_model import WeatherBlockModel


def _model_to_entity(m: WeatherBlockModel) -> WeatherBlockReport:
    """ORM model → domain entity mapping."""
    return WeatherBlockReport(
        weather_block_id=m.weather_block_id,
        mission_id=m.mission_id,
        field_id=uuid.UUID(int=0),  # weather_blocks tablosunda field_id yok; mission üzerinden elde edilir
        reported_at=m.created_at,
        reason=m.reason,
        created_at=m.created_at,
        block_start=None,
        block_end=None,
        notes=None,
        resolved=m.status == "VERIFIED",
    )


def _entity_to_model(e: WeatherBlockReport) -> WeatherBlockModel:
    """Domain entity → ORM model mapping."""
    model = WeatherBlockModel()
    model.weather_block_id = e.weather_block_id
    model.mission_id = e.mission_id
    model.pilot_id = uuid.UUID(int=0)  # caller must set pilot_id separately
    model.reason = e.reason
    model.status = "PENDING"
    return model


class WeatherBlockRepositoryImpl(WeatherBlockRepository):
    """WeatherBlockRepository portunun SQLAlchemy implementasyonu (KR-015-5)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, block: WeatherBlockReport) -> None:
        existing = await self._session.get(WeatherBlockModel, block.weather_block_id)
        if existing is not None:
            existing.reason = block.reason
            existing.status = "VERIFIED" if block.resolved else "PENDING"
        else:
            self._session.add(_entity_to_model(block))
        await self._session.flush()

    async def find_by_id(self, weather_block_id: uuid.UUID) -> Optional[WeatherBlockReport]:
        model = await self._session.get(WeatherBlockModel, weather_block_id)
        if model is None:
            return None
        return _model_to_entity(model)

    async def list_by_status(self, status: WeatherBlockStatus) -> List[WeatherBlockReport]:
        # Map domain status to DB enum
        db_status_map = {
            WeatherBlockStatus.REPORTED: "PENDING",
            WeatherBlockStatus.RESOLVED: "VERIFIED",
            WeatherBlockStatus.EXPIRED: "REJECTED",
        }
        db_status = db_status_map.get(status, "PENDING")
        stmt = select(WeatherBlockModel).where(WeatherBlockModel.status == db_status)
        result = await self._session.execute(stmt)
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def list_blocking_by_mission_id(self, mission_id: uuid.UUID) -> List[WeatherBlockReport]:
        stmt = select(WeatherBlockModel).where(
            WeatherBlockModel.mission_id == mission_id,
            WeatherBlockModel.status == "PENDING",
        )
        result = await self._session.execute(stmt)
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def list_by_field_id(
        self,
        field_id: uuid.UUID,
        *,
        status: Optional[WeatherBlockStatus] = None,
    ) -> List[WeatherBlockReport]:
        # weather_blocks has no direct field_id; join through missions
        from src.infrastructure.persistence.sqlalchemy.models.mission_model import MissionModel

        stmt = (
            select(WeatherBlockModel)
            .join(MissionModel, WeatherBlockModel.mission_id == MissionModel.mission_id)
            .where(MissionModel.field_id == field_id)
        )
        if status is not None:
            db_status_map = {
                WeatherBlockStatus.REPORTED: "PENDING",
                WeatherBlockStatus.RESOLVED: "VERIFIED",
                WeatherBlockStatus.EXPIRED: "REJECTED",
            }
            stmt = stmt.where(WeatherBlockModel.status == db_status_map.get(status, "PENDING"))
        result = await self._session.execute(stmt)
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def delete(self, weather_block_id: uuid.UUID) -> None:
        model = await self._session.get(WeatherBlockModel, weather_block_id)
        if model is None:
            raise KeyError(f"WeatherBlock not found: {weather_block_id}")
        await self._session.delete(model)
        await self._session.flush()
