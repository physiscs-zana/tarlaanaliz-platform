# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-028: MissionRepository SQLAlchemy implementation.
"""MissionRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.mission import Mission, MissionStatus
from src.infrastructure.persistence.sqlalchemy.models.mission_model import MissionModel


class MissionRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: MissionModel) -> Mission:
        return Mission(
            mission_id=model.mission_id,
            field_id=model.field_id,
            requested_by_user_id=model.requested_by_user_id,
            crop_type=model.crop_type,
            analysis_type=model.analysis_type,
            status=MissionStatus(model.status),
            price_snapshot_id=model.price_snapshot_id or uuid.UUID(int=0),
            created_at=model.created_at,
            subscription_id=model.subscription_id,
            payment_intent_id=model.payment_intent_id,
            planned_at=model.planned_at,
            due_at=model.due_at,
            flown_at=model.flown_at,
            uploaded_at=model.uploaded_at,
            analyzed_at=model.analyzed_at,
        )

    async def save(
        self,
        mission_id: uuid.UUID,
        field_id: uuid.UUID,
        user_id: uuid.UUID,
        crop_type: str,
        analysis_type: str = "MULTISPECTRAL",
        planned_at: datetime | None = None,
    ) -> MissionModel:
        model = MissionModel(
            mission_id=mission_id,
            field_id=field_id,
            requested_by_user_id=user_id,
            crop_type=crop_type,
            analysis_type=analysis_type,
            status="PLANNED",
            planned_at=planned_at or datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(model)
        await self._session.flush()
        return model

    async def find_by_id(self, mission_id: uuid.UUID) -> Optional[MissionModel]:
        return await self._session.get(MissionModel, mission_id)

    async def list_by_user_id(self, user_id: uuid.UUID) -> List[MissionModel]:
        result = await self._session.execute(
            select(MissionModel)
            .where(MissionModel.requested_by_user_id == user_id)
            .order_by(MissionModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_field_id(self, field_id: uuid.UUID) -> List[MissionModel]:
        result = await self._session.execute(
            select(MissionModel).where(MissionModel.field_id == field_id).order_by(MissionModel.created_at.desc())
        )
        return list(result.scalars().all())
