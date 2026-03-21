# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-029: FeedbackRecordRepository SQLAlchemy implementation.
"""FeedbackRecordRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.feedback_record import FeedbackRecord
from src.core.ports.repositories.feedback_record_repository import FeedbackRecordRepository
from src.infrastructure.persistence.sqlalchemy.models.feedback_record_model import FeedbackRecordModel


class FeedbackRecordRepositoryImpl(FeedbackRecordRepository):
    """FeedbackRecordRepository portunun async SQLAlchemy implementasyonu (KR-029, KR-019)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _to_entity(self, model: FeedbackRecordModel) -> FeedbackRecord:
        """ORM modelini domain entity'sine donusturur."""
        return FeedbackRecord(
            feedback_id=model.feedback_id,
            review_id=model.review_id,
            mission_id=model.mission_id,
            model_id=model.model_id,
            verdict=model.verdict,
            training_grade=model.training_grade,
            created_at=model.created_at,
            corrected_class=model.corrected_class,
            notes=model.notes,
            time_spent_seconds=model.time_spent_seconds,
            grade_reason=model.grade_reason,
            expert_confidence=Decimal(str(model.expert_confidence)) if model.expert_confidence is not None else None,
            image_quality=Decimal(str(model.image_quality)) if model.image_quality is not None else None,
            no_conflict=model.no_conflict,
        )

    def _apply_to_model(self, model: FeedbackRecordModel, entity: FeedbackRecord) -> None:
        """Entity alanlarini ORM modeline yazar."""
        model.feedback_id = entity.feedback_id
        model.review_id = entity.review_id
        model.mission_id = entity.mission_id
        model.model_id = entity.model_id
        model.verdict = entity.verdict
        model.training_grade = entity.training_grade
        model.created_at = entity.created_at
        model.corrected_class = entity.corrected_class
        model.notes = entity.notes
        model.time_spent_seconds = entity.time_spent_seconds
        model.grade_reason = entity.grade_reason
        model.expert_confidence = entity.expert_confidence
        model.image_quality = entity.image_quality
        model.no_conflict = entity.no_conflict

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------

    async def save(self, record: FeedbackRecord) -> None:
        """FeedbackRecord kaydet (insert veya update)."""
        existing = await self._session.get(FeedbackRecordModel, record.feedback_id)
        if existing:
            existing.verdict = record.verdict
            existing.training_grade = record.training_grade
            existing.corrected_class = record.corrected_class
            existing.notes = record.notes
            existing.time_spent_seconds = record.time_spent_seconds
            existing.grade_reason = record.grade_reason
            existing.expert_confidence = record.expert_confidence
            existing.image_quality = record.image_quality
            existing.no_conflict = record.no_conflict
        else:
            model = FeedbackRecordModel()
            self._apply_to_model(model, record)
            self._session.add(model)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------

    async def find_by_id(self, feedback_id: uuid.UUID) -> Optional[FeedbackRecord]:
        """feedback_id ile FeedbackRecord getir."""
        model = await self._session.get(FeedbackRecordModel, feedback_id)
        return self._to_entity(model) if model else None

    async def find_by_review_id(self, review_id: uuid.UUID) -> Optional[FeedbackRecord]:
        """review_id ile FeedbackRecord getir."""
        result = await self._session.execute(
            select(FeedbackRecordModel).where(FeedbackRecordModel.review_id == review_id)
        )
        model = result.scalars().first()
        return self._to_entity(model) if model else None

    # ------------------------------------------------------------------
    # Liste sorgulari
    # ------------------------------------------------------------------

    async def list_by_mission_id(self, mission_id: uuid.UUID) -> List[FeedbackRecord]:
        """Bir mission'a ait tum geri bildirimleri getir."""
        result = await self._session.execute(
            select(FeedbackRecordModel)
            .where(FeedbackRecordModel.mission_id == mission_id)
            .order_by(FeedbackRecordModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_model_id(self, model_id: str) -> List[FeedbackRecord]:
        """Belirli bir YZ modeline ait tum geri bildirimleri getir."""
        result = await self._session.execute(
            select(FeedbackRecordModel)
            .where(FeedbackRecordModel.model_id == model_id)
            .order_by(FeedbackRecordModel.created_at.asc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_verdict(self, verdict: str) -> List[FeedbackRecord]:
        """Belirli verdict'e gore geri bildirimleri getir."""
        result = await self._session.execute(
            select(FeedbackRecordModel)
            .where(FeedbackRecordModel.verdict == verdict)
            .order_by(FeedbackRecordModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_training_grade(self, training_grade: str) -> List[FeedbackRecord]:
        """Belirli egitim notuna gore geri bildirimleri getir."""
        result = await self._session.execute(
            select(FeedbackRecordModel)
            .where(FeedbackRecordModel.training_grade == training_grade)
            .order_by(FeedbackRecordModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------

    async def delete(self, feedback_id: uuid.UUID) -> None:
        """FeedbackRecord sil."""
        await self._session.execute(
            sa_delete(FeedbackRecordModel).where(FeedbackRecordModel.feedback_id == feedback_id)
        )
        await self._session.flush()
