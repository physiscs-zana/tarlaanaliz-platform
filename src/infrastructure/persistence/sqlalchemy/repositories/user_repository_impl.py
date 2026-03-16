# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-050: UserRepository SQLAlchemy implementation.
"""UserRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import delete as sa_delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.user import User, UserRole
from src.core.ports.repositories.user_repository import UserRepository
from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel


class UserRepositoryImpl(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: UserModel, role: UserRole = UserRole.FARMER_SINGLE) -> User:
        return User(
            user_id=model.user_id,
            phone_number=model.phone,
            pin_hash=model.pin_hash,
            role=role,
            province=model.province or "",
            created_at=model.created_at,
            updated_at=model.updated_at,
            must_reset_pin=model.must_change_pin,
            coop_id=None,
        )

    def _to_model(self, entity: User) -> UserModel:
        return UserModel(
            user_id=entity.user_id,
            phone=entity.phone_number,
            pin_hash=entity.pin_hash,
            first_name="",
            last_name="",
            province=entity.province,
            is_active=True,
            must_change_pin=entity.must_reset_pin,
        )

    async def save(self, user: User) -> None:
        existing = await self._session.get(UserModel, user.user_id)
        if existing:
            existing.phone = user.phone_number
            existing.pin_hash = user.pin_hash
            existing.province = user.province
            existing.must_change_pin = user.must_reset_pin
        else:
            model = self._to_model(user)
            self._session.add(model)
            # Also insert role
            await self._session.execute(
                text("INSERT INTO user_roles (user_id, role_code) VALUES (:uid, :role) ON CONFLICT DO NOTHING"),
                {"uid": str(user.user_id), "role": user.role.value},
            )
        await self._session.flush()

    async def find_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        model = await self._session.get(UserModel, user_id)
        if not model:
            return None
        role = await self._get_primary_role(user_id)
        return self._to_entity(model, role)

    async def find_by_phone_number(self, phone_number: str) -> Optional[User]:
        result = await self._session.execute(select(UserModel).where(UserModel.phone == phone_number))
        model = result.scalar_one_or_none()
        if not model:
            return None
        role = await self._get_primary_role(model.user_id)
        return self._to_entity(model, role)

    async def _get_primary_role(self, user_id: uuid.UUID) -> UserRole:
        result = await self._session.execute(
            text("SELECT role_code FROM user_roles WHERE user_id = :uid LIMIT 1"),
            {"uid": str(user_id)},
        )
        row = result.fetchone()
        if row:
            try:
                return UserRole(row[0])
            except ValueError:
                pass
        return UserRole.FARMER_SINGLE

    async def list_by_role(self, role: UserRole) -> List[User]:
        result = await self._session.execute(
            text("SELECT u.* FROM users u JOIN user_roles ur ON u.user_id = ur.user_id WHERE ur.role_code = :role"),
            {"role": role.value},
        )
        models = result.fetchall()
        return [self._to_entity(UserModel(**dict(row._mapping)), role) for row in models]

    async def list_by_province(self, province: str) -> List[User]:
        result = await self._session.execute(select(UserModel).where(UserModel.province == province))
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_coop_id(self, coop_id: uuid.UUID) -> List[User]:
        return []  # MVP: coop support deferred

    async def delete(self, user_id: uuid.UUID) -> None:
        await self._session.execute(sa_delete(UserModel).where(UserModel.user_id == user_id))
        await self._session.flush()
