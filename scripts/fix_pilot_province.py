"""Fix pilot province and service area for auto-dispatch."""
import asyncio
import sys
import uuid

from sqlalchemy import select

from src.infrastructure.persistence.sqlalchemy.models.pilot_model import PilotModel, PilotServiceAreaModel
from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
from src.infrastructure.persistence.sqlalchemy.session import get_async_session


async def fix(province: str):
    async with get_async_session() as session:
        pilots = (await session.execute(select(PilotModel))).scalars().all()
        for p in pilots:
            # Update pilot province
            p.province = province

            # Update user province
            user = (
                await session.execute(select(UserModel).where(UserModel.user_id == p.user_id))
            ).scalar_one_or_none()
            if user:
                user.province = province

            # Delete old service areas and create new one
            old_areas = (
                await session.execute(
                    select(PilotServiceAreaModel).where(PilotServiceAreaModel.pilot_id == p.pilot_id)
                )
            ).scalars().all()
            for a in old_areas:
                await session.delete(a)

            session.add(
                PilotServiceAreaModel(
                    service_area_id=uuid.uuid4(),
                    pilot_id=p.pilot_id,
                    province=province,
                    district="",
                )
            )
            print(f"Updated pilot {p.pilot_id}: province={province}, service_area={province}")

        await session.commit()
        print("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_pilot_province.py <PROVINCE>")
        print("Example: python fix_pilot_province.py Diyarbakir")
        sys.exit(1)
    asyncio.run(fix(sys.argv[1]))
