# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033: PaymentIntentRepository SQLAlchemy implementation.
# PATH: src/infrastructure/persistence/sqlalchemy/repositories/payment_intent_repository_impl.py
# DESC: PaymentIntentRepository portunun SQLAlchemy implementasyonu.
"""PaymentIntentRepository SQLAlchemy implementation (KR-033)."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.persistence.sqlalchemy.models.payment_intent_model import PaymentIntentModel


class PaymentIntentRepositoryImpl:
    """PaymentIntent DB operations backed by SQLAlchemy async sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, model: PaymentIntentModel) -> None:
        """Insert or merge a payment intent."""
        await self._session.merge(model)
        await self._session.flush()

    async def find_by_id(self, payment_intent_id: uuid.UUID) -> Optional[PaymentIntentModel]:
        result = await self._session.execute(
            select(PaymentIntentModel)
            .options(selectinload(PaymentIntentModel.payer))
            .where(PaymentIntentModel.payment_intent_id == payment_intent_id)
        )
        return result.scalar_one_or_none()

    async def list_by_status(self, status: str) -> list[PaymentIntentModel]:
        result = await self._session.execute(
            select(PaymentIntentModel)
            .options(selectinload(PaymentIntentModel.payer))
            .where(PaymentIntentModel.status == status)
            .order_by(PaymentIntentModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_payer(self, payer_user_id: uuid.UUID) -> list[PaymentIntentModel]:
        result = await self._session.execute(
            select(PaymentIntentModel)
            .where(PaymentIntentModel.payer_user_id == payer_user_id)
            .order_by(PaymentIntentModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[PaymentIntentModel]:
        result = await self._session.execute(
            select(PaymentIntentModel)
            .options(selectinload(PaymentIntentModel.payer))
            .order_by(PaymentIntentModel.created_at.desc())
        )
        return list(result.scalars().all())
