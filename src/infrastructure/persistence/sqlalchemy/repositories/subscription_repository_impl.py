# PATH: src/infrastructure/persistence/sqlalchemy/repositories/subscription_repository_impl.py
# DESC: SubscriptionRepository portunun SQLAlchemy async implementasyonu.
# SSOT: KR-027 (abonelik planlayici), KR-015-5 (tarama takvimi), KR-033 (odeme hard gate)
"""
SqlAlchemySubscriptionRepository — SubscriptionRepository portunu implemente eder.

Sorumluluk: Subscription entity'sinin async SQLAlchemy (AsyncSession) üzerinden
  kalıcı depolama okuma/yazma işlemleri.

KR-027: list_due() scheduler sorgusu — status=ACTIVE AND next_due_at <= now().
KR-033: PAID olmadan Subscription ACTIVE olamaz (ödeme doğrulama caller sorumluluğunda).
KR-015-5: Reschedule token alanları model üzerinden korunur.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.subscription import (
    Subscription,
    SubscriptionPlanType,
    SubscriptionStatus,
)
from src.core.ports.repositories.subscription_repository import SubscriptionRepository
from src.infrastructure.persistence.sqlalchemy.models.subscription_model import SubscriptionModel


class SqlAlchemySubscriptionRepository(SubscriptionRepository):
    """SubscriptionRepository portunun async SQLAlchemy implementasyonu (KR-027, KR-015-5, KR-033)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------

    async def save(self, subscription: Subscription) -> None:
        """Subscription kaydet veya guncelle (upsert via merge)."""
        model = await self._session.get(SubscriptionModel, subscription.subscription_id)
        if model is None:
            model = SubscriptionModel()
        self._apply_to_model(model, subscription)
        self._session.add(model)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------

    async def find_by_id(self, subscription_id: uuid.UUID) -> Optional[Subscription]:
        model = await self._session.get(SubscriptionModel, subscription_id)
        if model is None:
            return None
        return self._to_entity(model)

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------

    async def list_by_farmer_user_id(
        self,
        farmer_user_id: uuid.UUID,
        *,
        status: Optional[SubscriptionStatus] = None,
    ) -> List[Subscription]:
        stmt = select(SubscriptionModel).where(SubscriptionModel.farmer_user_id == farmer_user_id)
        if status is not None:
            stmt = stmt.where(SubscriptionModel.status == status.value)
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def list_by_field_id(self, field_id: uuid.UUID) -> List[Subscription]:
        stmt = select(SubscriptionModel).where(SubscriptionModel.field_id == field_id)
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def list_by_status(self, status: SubscriptionStatus) -> List[Subscription]:
        stmt = select(SubscriptionModel).where(SubscriptionModel.status == status.value)
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def list_due(self) -> List[Subscription]:
        """Zamanı gelmiş (due) abonelikleri getir (KR-027 scheduler).

        status=ACTIVE ve next_due_at <= now olan abonelikleri döner.
        """
        now = datetime.now(timezone.utc)
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.status == SubscriptionStatus.ACTIVE.value,
            SubscriptionModel.next_due_at <= now,
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------

    async def delete(self, subscription_id: uuid.UUID) -> None:
        model = await self._session.get(SubscriptionModel, subscription_id)
        if model is None:
            raise KeyError(f"Subscription not found: {subscription_id}")
        await self._session.delete(model)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Mapping yardımcıları
    # ------------------------------------------------------------------

    def _apply_to_model(self, model: SubscriptionModel, entity: Subscription) -> None:
        """Entity alanlarını ORM modeline yazar."""
        model.subscription_id = entity.subscription_id
        model.farmer_user_id = entity.farmer_user_id
        model.field_id = entity.field_id
        model.crop_type = entity.crop_type
        model.analysis_type = entity.analysis_type
        model.interval_days = entity.interval_days
        model.start_date = entity.start_date
        model.end_date = entity.end_date
        model.next_due_at = entity.next_due_at
        model.status = entity.status.value
        model.price_snapshot_id = entity.price_snapshot_id
        model.payment_intent_id = entity.payment_intent_id
        model.plan_type = entity.plan_type.value
        model.reschedule_tokens_per_season = entity.reschedule_tokens_per_season
        # KR-015-5: remaining = per_season - used
        model.reschedule_tokens_remaining = entity.remaining_reschedule_tokens
        model.created_at = entity.created_at
        model.updated_at = entity.updated_at

    def _to_entity(self, model: SubscriptionModel) -> Subscription:
        """ORM modelini domain entity'sine dönüştürür."""
        per_season: int = model.reschedule_tokens_per_season or 2
        remaining: int = model.reschedule_tokens_remaining
        tokens_used: int = max(0, per_season - remaining)

        return Subscription(
            subscription_id=model.subscription_id,
            farmer_user_id=model.farmer_user_id,
            field_id=model.field_id,
            crop_type=model.crop_type,
            analysis_type=model.analysis_type,
            interval_days=model.interval_days,
            start_date=model.start_date,
            end_date=model.end_date,
            next_due_at=model.next_due_at,
            status=SubscriptionStatus(model.status),
            price_snapshot_id=model.price_snapshot_id,
            payment_intent_id=model.payment_intent_id,
            plan_type=SubscriptionPlanType(model.plan_type) if model.plan_type else SubscriptionPlanType.SEASONAL,
            reschedule_tokens_per_season=per_season,
            reschedule_tokens_used=tokens_used,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
