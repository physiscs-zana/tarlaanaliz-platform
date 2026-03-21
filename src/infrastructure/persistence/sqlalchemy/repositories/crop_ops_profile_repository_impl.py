# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015-1: CropOpsProfileRepository SQLAlchemy implementation.
"""CropOpsProfileRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.value_objects.crop_ops_profile import CropOpsProfile
from src.core.domain.value_objects.crop_type import CropType
from src.core.ports.repositories.crop_ops_profile_repository import CropOpsProfileRepository
from src.infrastructure.persistence.models.crop_ops_profile_model import CropOpsProfileModel


class CropOpsProfileRepositoryImpl(CropOpsProfileRepository):
    """CropOpsProfileRepository portunun async SQLAlchemy implementasyonu (KR-015-1)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------

    async def save(self, profile: CropOpsProfile) -> None:
        """Profil kaydi olustur veya guncelle."""
        result = await self._session.execute(
            select(CropOpsProfileModel).where(CropOpsProfileModel.crop_type == profile.crop_type.code)
        )
        existing = result.scalars().first()
        if existing:
            existing.update_from_domain(profile)
        else:
            model = CropOpsProfileModel.from_domain(profile)
            self._session.add(model)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------

    async def get_by_crop_type(self, crop_type: CropType) -> Optional[CropOpsProfile]:
        """Bitki turune gore profil getir. Bulunamazsa None doner."""
        result = await self._session.execute(
            select(CropOpsProfileModel).where(CropOpsProfileModel.crop_type == crop_type.code)
        )
        model = result.scalars().first()
        return model.to_domain() if model else None

    # ------------------------------------------------------------------
    # Liste sorgulari
    # ------------------------------------------------------------------

    async def get_all(self) -> List[CropOpsProfile]:
        """Tum profilleri getir."""
        result = await self._session.execute(
            select(CropOpsProfileModel).order_by(CropOpsProfileModel.crop_type)
        )
        return [m.to_domain() for m in result.scalars().all()]

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------

    async def delete(self, crop_type: CropType) -> None:
        """Bitki turune gore profili sil."""
        await self._session.execute(
            sa_delete(CropOpsProfileModel).where(CropOpsProfileModel.crop_type == crop_type.code)
        )
        await self._session.flush()
