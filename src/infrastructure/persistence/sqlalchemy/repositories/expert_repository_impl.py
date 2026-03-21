# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-019: ExpertRepository SQLAlchemy implementation.
"""ExpertRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.expert import Expert, ExpertStatus
from src.core.ports.repositories.expert_repository import ExpertRepository
from src.infrastructure.persistence.sqlalchemy.models.expert_model import ExpertModel


class ExpertRepositoryImpl(ExpertRepository):
    """ExpertRepository portunun async SQLAlchemy implementasyonu (KR-019)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _to_entity(self, model: ExpertModel) -> Expert:
        """ORM modelini domain entity'sine donusturur."""
        return Expert(
            expert_id=model.expert_id,
            user_id=model.user_id,
            province=model.province,
            max_daily_quota=model.max_daily_quota,
            specialization=list(model.specialization) if model.specialization else [],
            status=ExpertStatus(model.status),
            created_by_admin_user_id=model.created_by_admin_user_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _apply_to_model(self, model: ExpertModel, entity: Expert) -> None:
        """Entity alanlarini ORM modeline yazar."""
        model.expert_id = entity.expert_id
        model.user_id = entity.user_id
        model.province = entity.province
        model.max_daily_quota = entity.max_daily_quota
        model.specialization = entity.specialization
        model.status = entity.status.value
        model.created_by_admin_user_id = entity.created_by_admin_user_id
        model.created_at = entity.created_at
        model.updated_at = entity.updated_at

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------

    async def save(self, expert: Expert) -> None:
        """Expert kaydet (insert veya update)."""
        existing = await self._session.get(ExpertModel, expert.expert_id)
        if existing:
            existing.province = expert.province
            existing.max_daily_quota = expert.max_daily_quota
            existing.specialization = expert.specialization
            existing.status = expert.status.value
            existing.updated_at = expert.updated_at
        else:
            model = ExpertModel()
            self._apply_to_model(model, expert)
            self._session.add(model)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------

    async def find_by_id(self, expert_id: uuid.UUID) -> Optional[Expert]:
        """expert_id ile Expert getir."""
        model = await self._session.get(ExpertModel, expert_id)
        return self._to_entity(model) if model else None

    async def find_by_user_id(self, user_id: uuid.UUID) -> Optional[Expert]:
        """user_id ile Expert getir."""
        result = await self._session.execute(select(ExpertModel).where(ExpertModel.user_id == user_id))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    # ------------------------------------------------------------------
    # Liste sorgulari
    # ------------------------------------------------------------------

    async def list_by_province(self, province: str) -> List[Expert]:
        """Belirli bir ildeki uzmanlari getir."""
        result = await self._session.execute(
            select(ExpertModel).where(ExpertModel.province == province).order_by(ExpertModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_status(self, status: ExpertStatus) -> List[Expert]:
        """Belirli durumdaki uzmanlari getir."""
        result = await self._session.execute(
            select(ExpertModel).where(ExpertModel.status == status.value).order_by(ExpertModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_specialization(self, specialization: str) -> List[Expert]:
        """Belirli uzmanlik alanindaki uzmanlari getir (PostgreSQL ARRAY contains)."""
        result = await self._session.execute(
            select(ExpertModel)
            .where(ExpertModel.specialization.contains([specialization]))
            .order_by(ExpertModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------

    async def delete(self, expert_id: uuid.UUID) -> None:
        """Expert sil."""
        await self._session.execute(sa_delete(ExpertModel).where(ExpertModel.expert_id == expert_id))
        await self._session.flush()
