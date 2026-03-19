# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-013: FieldRepository SQLAlchemy implementation.
"""FieldRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.field import Field, FieldStatus
from src.core.ports.repositories.field_repository import FieldRepository
from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel


class FieldRepositoryImpl(FieldRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: FieldModel) -> Field:
        return Field(
            field_id=model.field_id,
            user_id=model.user_id,
            province=model.province,
            district=model.district,
            village=model.village,
            ada=model.block_no,
            parsel=model.parcel_no,
            area_m2=model.area_m2,
            status=FieldStatus.ACTIVE if model.is_active else FieldStatus.INACTIVE,
            created_at=model.created_at,
            updated_at=model.updated_at,
            crop_type=model.crop_type,
            field_code=model.field_code,
            geometry=None,  # geometry stored as PostGIS, simplified for MVP
        )

    def _to_model(self, entity: Field) -> FieldModel:
        return FieldModel(
            field_id=entity.field_id,
            user_id=entity.user_id,
            province=entity.province,
            district=entity.district,
            village=entity.village,
            block_no=entity.ada,
            parcel_no=entity.parsel,
            area_m2=entity.area_m2,
            area_donum=entity.area_m2 / Decimal("1000"),
            crop_type=entity.crop_type,
            is_active=entity.status == FieldStatus.ACTIVE,
        )

    async def save(self, field: Field) -> None:
        existing = await self._session.get(FieldModel, field.field_id)
        if existing:
            existing.province = field.province
            existing.district = field.district
            existing.village = field.village
            existing.block_no = field.ada
            existing.parcel_no = field.parsel
            existing.area_m2 = field.area_m2
            existing.area_donum = field.area_m2 / Decimal("1000")
            existing.crop_type = field.crop_type
            existing.is_active = field.status == FieldStatus.ACTIVE
        else:
            self._session.add(self._to_model(field))
        await self._session.flush()

    async def find_by_id(self, field_id: uuid.UUID) -> Optional[Field]:
        model = await self._session.get(FieldModel, field_id)
        return self._to_entity(model) if model else None

    async def find_by_parcel_ref(
        self, province: str, district: str, village: str, ada: str, parsel: str
    ) -> Optional[Field]:
        result = await self._session.execute(
            select(FieldModel).where(
                FieldModel.province == province,
                FieldModel.district == district,
                FieldModel.village == village,
                FieldModel.block_no == ada,
                FieldModel.parcel_no == parsel,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_user_id(self, user_id: uuid.UUID) -> List[Field]:
        result = await self._session.execute(
            select(FieldModel).where(FieldModel.user_id == user_id).order_by(FieldModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_province(self, province: str) -> List[Field]:
        result = await self._session.execute(select(FieldModel).where(FieldModel.province == province))
        return [self._to_entity(m) for m in result.scalars().all()]

    async def delete(self, field_id: uuid.UUID) -> None:
        await self._session.execute(sa_delete(FieldModel).where(FieldModel.field_id == field_id))
        await self._session.flush()
