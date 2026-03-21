"""Check pilot service areas and auto-dispatch readiness."""
import asyncio

from sqlalchemy import select

from src.infrastructure.persistence.sqlalchemy.models.pilot_model import PilotModel, PilotServiceAreaModel
from src.infrastructure.persistence.sqlalchemy.session import get_async_session


async def check():
    async with get_async_session() as s:
        pilots = (await s.execute(select(PilotModel))).scalars().all()
        for p in pilots:
            areas = (
                await s.execute(
                    select(PilotServiceAreaModel).where(
                        PilotServiceAreaModel.pilot_id == p.pilot_id
                    )
                )
            ).scalars().all()
            print(
                f"Pilot: {p.province} | active={p.is_active} "
                f"| capacity={p.daily_capacity_donum} "
                f"| service_areas={[a.province for a in areas]}"
            )
        if not pilots:
            print("No pilots in pilots table")


if __name__ == "__main__":
    asyncio.run(check())
