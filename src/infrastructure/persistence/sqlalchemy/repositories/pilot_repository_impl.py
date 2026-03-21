# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015: PilotRepository SQLAlchemy implementation.
"""PilotRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.pilot import Pilot, PilotStatus
from src.core.ports.repositories.pilot_repository import PilotRepository
from src.infrastructure.persistence.sqlalchemy.models.pilot_model import PilotModel


class PilotRepositoryImpl(PilotRepository):
    """PilotRepository portunun async SQLAlchemy implementasyonu (KR-015)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _to_entity(self, model: PilotModel) -> Pilot:
        """ORM modelini domain entity'sine donusturur."""
        # ORM work_days ARRAY(String) -> entity work_days List[int]
        work_days_int: List[int] = []
        if model.work_days:
            _DAY_MAP = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
            for d in model.work_days:
                if d in _DAY_MAP:
                    work_days_int.append(_DAY_MAP[d])
                elif d.isdigit():
                    work_days_int.append(int(d))

        # user relationship icinden display_name
        full_name = ""
        phone_number = ""
        if model.user:
            full_name = f"{model.user.first_name or ''} {model.user.last_name or ''}".strip()
            phone_number = model.user.phone or ""

        # PilotServiceAreaModel'den province_list olustur
        province_list: List[str] = []
        if hasattr(model, 'service_areas') and model.service_areas:
            province_list = list({sa.province for sa in model.service_areas})

        return Pilot(
            pilot_id=model.pilot_id,
            user_id=model.user_id,
            province=model.province,
            district=model.district or "",
            full_name=full_name or "Pilot",
            phone_number=phone_number,
            drone_model=model.drone_model,
            drone_serial_number=model.drone_serial_no,
            work_days=work_days_int,
            daily_capacity_donum=model.daily_capacity_donum,
            system_seed_quota=model.system_seed_quota,
            province_list=province_list,
            reliability_score=Decimal(str(model.reliability_score)),
            status=PilotStatus.ACTIVE if model.is_active else PilotStatus.INACTIVE,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _work_days_to_str(self, days: List[int]) -> list[str]:
        """Entity int days -> ORM string days."""
        _DAY_MAP = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
        return [_DAY_MAP.get(d, str(d)) for d in days]

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------

    async def save(self, pilot: Pilot) -> None:
        """Pilot kaydet (insert veya update)."""
        existing = await self._session.get(PilotModel, pilot.pilot_id)
        if existing:
            existing.province = pilot.province
            existing.district = pilot.district
            existing.drone_model = pilot.drone_model
            existing.drone_serial_no = pilot.drone_serial_number
            existing.work_days = self._work_days_to_str(pilot.work_days)
            existing.daily_capacity_donum = pilot.daily_capacity_donum
            existing.system_seed_quota = pilot.system_seed_quota
            existing.reliability_score = pilot.reliability_score
            existing.is_active = pilot.status == PilotStatus.ACTIVE
        else:
            model = PilotModel(
                pilot_id=pilot.pilot_id,
                user_id=pilot.user_id,
                province=pilot.province,
                district=pilot.district,
                drone_model=pilot.drone_model,
                drone_serial_no=pilot.drone_serial_number,
                work_days=self._work_days_to_str(pilot.work_days),
                daily_capacity_donum=pilot.daily_capacity_donum,
                system_seed_quota=pilot.system_seed_quota,
                reliability_score=pilot.reliability_score,
                is_active=pilot.status == PilotStatus.ACTIVE,
            )
            self._session.add(model)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------

    async def find_by_id(self, pilot_id: uuid.UUID) -> Optional[Pilot]:
        """pilot_id ile Pilot getir."""
        model = await self._session.get(PilotModel, pilot_id)
        return self._to_entity(model) if model else None

    async def find_by_user_id(self, user_id: uuid.UUID) -> Optional[Pilot]:
        """user_id ile Pilot getir."""
        result = await self._session.execute(
            select(PilotModel).where(PilotModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    # ------------------------------------------------------------------
    # Liste sorgulari
    # ------------------------------------------------------------------

    async def list_by_province(self, province: str) -> List[Pilot]:
        """Belirli bir ildeki pilotlari getir."""
        result = await self._session.execute(
            select(PilotModel).where(PilotModel.province == province).order_by(PilotModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_status(self, status: PilotStatus) -> List[Pilot]:
        """Belirli durumdaki pilotlari getir."""
        is_active = status == PilotStatus.ACTIVE
        result = await self._session.execute(
            select(PilotModel).where(PilotModel.is_active == is_active).order_by(PilotModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_active_by_province(self, province: str) -> List[Pilot]:
        """Belirli bir ildeki aktif pilotlari getir (gorev atamasi icin)."""
        result = await self._session.execute(
            select(PilotModel).where(
                PilotModel.province == province,
                PilotModel.is_active.is_(True),
            ).order_by(PilotModel.reliability_score.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------

    async def delete(self, pilot_id: uuid.UUID) -> None:
        """Pilot sil."""
        await self._session.execute(sa_delete(PilotModel).where(PilotModel.pilot_id == pilot_id))
        await self._session.flush()
