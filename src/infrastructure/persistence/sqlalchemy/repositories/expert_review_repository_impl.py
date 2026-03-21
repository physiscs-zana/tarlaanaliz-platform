# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-019: ExpertReviewRepository SQLAlchemy implementation.
# KR-029: Training feedback verdict + training_grade.
"""ExpertReviewRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.expert_review import ExpertReview, ExpertReviewStatus
from src.core.ports.repositories.expert_review_repository import ExpertReviewRepository
from src.infrastructure.persistence.sqlalchemy.models.expert_review_model import ExpertReviewModel


class ExpertReviewRepositoryImpl(ExpertReviewRepository):
    """ExpertReviewRepository portunun async SQLAlchemy implementasyonu (KR-019, KR-029)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _to_entity(self, model: ExpertReviewModel) -> ExpertReview:
        """ORM modelini domain entity'sine donusturur."""
        return ExpertReview(
            review_id=model.review_id,
            mission_id=model.mission_id,
            expert_id=model.expert_id,
            analysis_result_id=model.analysis_result_id,
            status=ExpertReviewStatus(model.status),
            assigned_at=model.assigned_at,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            verdict=model.verdict,
            training_grade=model.training_grade,
            grade_reason=model.grade_reason,
        )

    def _apply_to_model(self, model: ExpertReviewModel, entity: ExpertReview) -> None:
        """Entity alanlarini ORM modeline yazar."""
        model.review_id = entity.review_id
        model.mission_id = entity.mission_id
        model.expert_id = entity.expert_id
        model.analysis_result_id = entity.analysis_result_id
        model.status = entity.status.value
        model.assigned_at = entity.assigned_at
        model.created_at = entity.created_at
        model.started_at = entity.started_at
        model.completed_at = entity.completed_at
        model.verdict = entity.verdict
        model.training_grade = entity.training_grade
        model.grade_reason = entity.grade_reason

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------

    async def save(self, review: ExpertReview) -> None:
        """ExpertReview kaydet (insert veya update)."""
        existing = await self._session.get(ExpertReviewModel, review.review_id)
        if existing:
            existing.status = review.status.value
            existing.started_at = review.started_at
            existing.completed_at = review.completed_at
            existing.verdict = review.verdict
            existing.training_grade = review.training_grade
            existing.grade_reason = review.grade_reason
        else:
            model = ExpertReviewModel()
            self._apply_to_model(model, review)
            self._session.add(model)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------

    async def find_by_id(self, review_id: uuid.UUID) -> Optional[ExpertReview]:
        """review_id ile ExpertReview getir."""
        model = await self._session.get(ExpertReviewModel, review_id)
        return self._to_entity(model) if model else None

    # ------------------------------------------------------------------
    # Liste sorgulari
    # ------------------------------------------------------------------

    async def list_by_expert_id(
        self,
        expert_id: uuid.UUID,
        *,
        status: Optional[ExpertReviewStatus] = None,
    ) -> List[ExpertReview]:
        """Bir uzmana ait incelemeleri getir (KR-019 ownership check)."""
        stmt = select(ExpertReviewModel).where(ExpertReviewModel.expert_id == expert_id)
        if status is not None:
            stmt = stmt.where(ExpertReviewModel.status == status.value)
        stmt = stmt.order_by(ExpertReviewModel.assigned_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_mission_id(self, mission_id: uuid.UUID) -> List[ExpertReview]:
        """Bir mission'a ait tum uzman incelemelerini getir."""
        result = await self._session.execute(
            select(ExpertReviewModel)
            .where(ExpertReviewModel.mission_id == mission_id)
            .order_by(ExpertReviewModel.assigned_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_analysis_result_id(self, analysis_result_id: uuid.UUID) -> List[ExpertReview]:
        """Bir analiz sonucuna ait tum uzman incelemelerini getir."""
        result = await self._session.execute(
            select(ExpertReviewModel)
            .where(ExpertReviewModel.analysis_result_id == analysis_result_id)
            .order_by(ExpertReviewModel.assigned_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_status(self, status: ExpertReviewStatus) -> List[ExpertReview]:
        """Belirli durumdaki tum incelemeleri getir (kuyruk yonetimi)."""
        result = await self._session.execute(
            select(ExpertReviewModel)
            .where(ExpertReviewModel.status == status.value)
            .order_by(ExpertReviewModel.assigned_at.asc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------

    async def delete(self, review_id: uuid.UUID) -> None:
        """ExpertReview sil."""
        await self._session.execute(sa_delete(ExpertReviewModel).where(ExpertReviewModel.review_id == review_id))
        await self._session.flush()
