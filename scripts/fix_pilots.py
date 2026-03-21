"""One-time script: create PilotModel + PilotServiceAreaModel for existing pilot users."""
import asyncio
import uuid

from sqlalchemy import select

from src.infrastructure.persistence.sqlalchemy.models.pilot_model import PilotModel, PilotServiceAreaModel
from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
from src.infrastructure.persistence.sqlalchemy.models.user_role_model import UserRoleModel
from src.infrastructure.persistence.sqlalchemy.session import get_async_session


async def fix_pilots():
    async with get_async_session() as session:
        result = await session.execute(
            select(UserModel)
            .join(UserRoleModel, UserModel.user_id == UserRoleModel.user_id)
            .where(UserRoleModel.role == "PILOT")
        )
        pilot_users = result.scalars().unique().all()
        fixed = 0
        for u in pilot_users:
            existing = await session.execute(
                select(PilotModel).where(PilotModel.user_id == u.user_id)
            )
            if existing.scalar_one_or_none() is None:
                pid = uuid.uuid4()
                session.add(
                    PilotModel(
                        pilot_id=pid,
                        user_id=u.user_id,
                        province=u.province or "",
                        drone_serial_no=f"DRONE-{uuid.uuid4().hex[:8].upper()}",
                    )
                )
                session.add(
                    PilotServiceAreaModel(
                        service_area_id=uuid.uuid4(),
                        pilot_id=pid,
                        province=u.province or "",
                        district="",
                    )
                )
                fixed += 1
                print(f"Fixed pilot: {u.display_name} ({u.province})")
        await session.commit()
        print(f"Done. {fixed} pilot(s) fixed out of {len(pilot_users)} total.")


if __name__ == "__main__":
    asyncio.run(fix_pilots())
