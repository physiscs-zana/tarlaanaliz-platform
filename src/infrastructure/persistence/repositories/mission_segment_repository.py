# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015: MissionSegment repository — segment CRUD operations.
"""MissionSegment repository implementation."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.sqlalchemy.models.mission_segment_model import (
    MissionSegmentModel,
)


class MissionSegmentRepository:
    """MissionSegment persistence (KR-015)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_many(self, segments: Sequence[MissionSegmentModel]) -> None:
        self._session.add_all(list(segments))
        await self._session.flush()
