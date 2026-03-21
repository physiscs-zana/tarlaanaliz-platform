# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: AnalysisResultRepository SQLAlchemy implementation.
# KR-025: YZ analiz sonuclari; ilaclama karari VERMEZ.
"""AnalysisResultRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.analysis_result import AnalysisResult
from src.core.ports.repositories.analysis_result_repository import AnalysisResultRepository
from src.infrastructure.persistence.sqlalchemy.models.analysis_result_model import AnalysisResultModel


class AnalysisResultRepositoryImpl(AnalysisResultRepository):
    """AnalysisResultRepository portunun async SQLAlchemy implementasyonu (KR-081, KR-025)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _to_entity(self, model: AnalysisResultModel) -> AnalysisResult:
        """ORM modelini domain entity'sine donusturur."""
        return AnalysisResult(
            result_id=model.result_id,
            analysis_job_id=model.analysis_job_id,
            mission_id=model.mission_id,
            field_id=model.field_id,
            overall_health_index=Decimal(str(model.overall_health_index)),
            findings=model.findings,
            summary=model.summary,
            report_tier=model.report_tier,
            band_class=model.band_class,
            available_layers=tuple(model.available_layers) if model.available_layers else (),
            thermal_summary=model.thermal_summary,
            created_at=model.created_at,
        )

    def _to_model(self, entity: AnalysisResult) -> AnalysisResultModel:
        """Domain entity'sini ORM modeline donusturur."""
        return AnalysisResultModel(
            result_id=entity.result_id,
            analysis_job_id=entity.analysis_job_id,
            mission_id=entity.mission_id,
            field_id=entity.field_id,
            overall_health_index=entity.overall_health_index,
            findings=entity.findings if isinstance(entity.findings, (dict, list)) else {},
            summary=entity.summary,
            report_tier=entity.report_tier,
            band_class=entity.band_class,
            available_layers=list(entity.available_layers),
            thermal_summary=entity.thermal_summary,
            created_at=entity.created_at,
        )

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------

    async def save(self, result: AnalysisResult) -> None:
        """AnalysisResult kaydet (insert veya update)."""
        existing = await self._session.get(AnalysisResultModel, result.result_id)
        if existing:
            existing.overall_health_index = result.overall_health_index
            existing.findings = result.findings if isinstance(result.findings, dict) else {}
            existing.summary = result.summary
            existing.report_tier = result.report_tier
            existing.band_class = result.band_class
            existing.available_layers = list(result.available_layers)
            existing.thermal_summary = result.thermal_summary
        else:
            self._session.add(self._to_model(result))
        await self._session.flush()

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------

    async def find_by_id(self, result_id: uuid.UUID) -> Optional[AnalysisResult]:
        """result_id ile AnalysisResult getir."""
        model = await self._session.get(AnalysisResultModel, result_id)
        return self._to_entity(model) if model else None

    async def find_by_analysis_job_id(self, analysis_job_id: uuid.UUID) -> Optional[AnalysisResult]:
        """analysis_job_id ile AnalysisResult getir."""
        result = await self._session.execute(
            select(AnalysisResultModel).where(AnalysisResultModel.analysis_job_id == analysis_job_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    # ------------------------------------------------------------------
    # Liste sorgulari
    # ------------------------------------------------------------------

    async def list_by_mission_id(self, mission_id: uuid.UUID) -> List[AnalysisResult]:
        """Bir mission'a ait tum analiz sonuclarini getir."""
        result = await self._session.execute(
            select(AnalysisResultModel)
            .where(AnalysisResultModel.mission_id == mission_id)
            .order_by(AnalysisResultModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_field_id(self, field_id: uuid.UUID) -> List[AnalysisResult]:
        """Bir tarlaya ait tum analiz sonuclarini getir."""
        result = await self._session.execute(
            select(AnalysisResultModel)
            .where(AnalysisResultModel.field_id == field_id)
            .order_by(AnalysisResultModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------

    async def delete(self, result_id: uuid.UUID) -> None:
        """AnalysisResult sil."""
        await self._session.execute(sa_delete(AnalysisResultModel).where(AnalysisResultModel.result_id == result_id))
        await self._session.flush()
