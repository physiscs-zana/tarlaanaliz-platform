# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-022: PriceSnapshotRepository SQLAlchemy implementation.
# KR-033: Fiyat snapshot immutable; siparis/abonelik olusurken siparise yazilir.
"""PriceSnapshotRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.price_snapshot import PriceSnapshot
from src.core.ports.repositories.price_snapshot_repository import PriceSnapshotRepository
from src.infrastructure.persistence.sqlalchemy.models.price_snapshot_model import PriceSnapshotModel


class PriceSnapshotRepositoryImpl(PriceSnapshotRepository):
    """PriceSnapshotRepository portunun async SQLAlchemy implementasyonu (KR-022, KR-033)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _to_entity(self, model: PriceSnapshotModel) -> PriceSnapshot:
        """ORM modelini domain entity'sine donusturur."""
        return PriceSnapshot(
            price_snapshot_id=model.price_snapshot_id,
            crop_type=model.crop_type,
            analysis_type=model.analysis_type,
            amount_kurus=model.unit_price_kurus,
            currency=model.currency,
            effective_date=model.effective_from.date()
            if isinstance(model.effective_from, datetime)
            else model.effective_from,
            created_at=model.created_at,
            promotional_discount_percent=Decimal(str(model.discount_pct)) if model.discount_pct is not None else None,
            effective_until=model.effective_to.date()
            if isinstance(model.effective_to, datetime)
            else model.effective_to,
            created_by_admin_user_id=model.created_by,
        )

    # ------------------------------------------------------------------
    # Kaydetme (insert only — PriceSnapshot immutable)
    # ------------------------------------------------------------------

    async def save(self, snapshot: PriceSnapshot) -> None:
        """PriceSnapshot kaydet (yalnizca insert; immutable — KR-022)."""
        model = PriceSnapshotModel(
            price_snapshot_id=snapshot.price_snapshot_id,
            crop_type=snapshot.crop_type,
            analysis_type=snapshot.analysis_type,
            unit_price_kurus=snapshot.amount_kurus,
            currency=snapshot.currency,
            discount_pct=snapshot.promotional_discount_percent,
            effective_from=snapshot.effective_date,
            effective_to=snapshot.effective_until,
            created_by=snapshot.created_by_admin_user_id,
        )
        self._session.add(model)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------

    async def find_by_id(self, price_snapshot_id: uuid.UUID) -> Optional[PriceSnapshot]:
        """price_snapshot_id ile PriceSnapshot getir."""
        model = await self._session.get(PriceSnapshotModel, price_snapshot_id)
        return self._to_entity(model) if model else None

    async def find_active_by_crop_and_type(
        self,
        crop_type: str,
        analysis_type: str,
        as_of: date,
    ) -> Optional[PriceSnapshot]:
        """Urun turu ve analiz turu icin belirli tarihte gecerli snapshot getir (KR-033)."""
        stmt = (
            select(PriceSnapshotModel)
            .where(
                PriceSnapshotModel.crop_type == crop_type,
                PriceSnapshotModel.analysis_type == analysis_type,
                PriceSnapshotModel.effective_from <= as_of,
            )
            .where((PriceSnapshotModel.effective_to.is_(None)) | (PriceSnapshotModel.effective_to >= as_of))
            .order_by(PriceSnapshotModel.effective_from.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    # ------------------------------------------------------------------
    # Liste sorgulari
    # ------------------------------------------------------------------

    async def list_by_crop_type(self, crop_type: str) -> List[PriceSnapshot]:
        """Bir urun turune ait tum fiyat snapshot'larini getir."""
        result = await self._session.execute(
            select(PriceSnapshotModel)
            .where(PriceSnapshotModel.crop_type == crop_type)
            .order_by(PriceSnapshotModel.effective_from.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_analysis_type(self, analysis_type: str) -> List[PriceSnapshot]:
        """Belirli analiz turundeki tum fiyat snapshot'larini getir."""
        result = await self._session.execute(
            select(PriceSnapshotModel)
            .where(PriceSnapshotModel.analysis_type == analysis_type)
            .order_by(PriceSnapshotModel.effective_from.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_active_as_of(self, as_of: date) -> List[PriceSnapshot]:
        """Belirli tarihte gecerli olan tum fiyat snapshot'larini getir."""
        result = await self._session.execute(
            select(PriceSnapshotModel)
            .where(
                PriceSnapshotModel.effective_from <= as_of,
                (PriceSnapshotModel.effective_to.is_(None)) | (PriceSnapshotModel.effective_to >= as_of),
            )
            .order_by(PriceSnapshotModel.effective_from.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------

    async def delete(self, price_snapshot_id: uuid.UUID) -> None:
        """PriceSnapshot sil."""
        await self._session.execute(
            sa_delete(PriceSnapshotModel).where(PriceSnapshotModel.price_snapshot_id == price_snapshot_id)
        )
        await self._session.flush()
