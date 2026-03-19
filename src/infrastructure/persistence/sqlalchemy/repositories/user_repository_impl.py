# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-050: UserRepository SQLAlchemy implementation.
# KR-063: Role management via ORM relationship (no raw SQL).
"""UserRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.user import User, UserRole
from src.core.ports.repositories.user_repository import UserRepository
from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
from src.infrastructure.persistence.sqlalchemy.models.user_role_model import UserRoleModel


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
            first_name=model.first_name or "",
            last_name=model.last_name or "",
            must_reset_pin=model.must_change_pin,
            coop_id=None,
        )

    def _to_model(self, entity: User) -> UserModel:
        model = UserModel(
            user_id=entity.user_id,
            phone=entity.phone_number,
            pin_hash=entity.pin_hash,
            first_name=entity.first_name,
            last_name=entity.last_name,
            province=entity.province,
            is_active=True,
            must_change_pin=entity.must_reset_pin,
        )
        # KR-063: role assignment through ORM relationship — no raw SQL needed
        model.roles = [UserRoleModel(user_id=entity.user_id, role=entity.role.value)]
        return model

    # Highest-privilege first — matches frontend ROLE_PRIORITY in useAuth.ts
    _ROLE_PRIORITY: list[str] = [
        "CENTRAL_ADMIN",
        "BILLING_ADMIN",
        "STATION_OPERATOR",
        "IL_OPERATOR",
        "EXPERT",
        "PILOT",
        "COOP_OWNER",
        "COOP_ADMIN",
        "COOP_AGRONOMIST",
        "COOP_VIEWER",
        "FARMER_SINGLE",
        "FARMER_MEMBER",
        "AI_SERVICE",
    ]

    @staticmethod
    def _primary_role_from_model(model: UserModel) -> UserRole:
        """Extract highest-privilege role from the eagerly loaded roles relationship."""
        if not model.roles:
            return UserRole.FARMER_SINGLE
        role_set = {r.role for r in model.roles}
        for candidate in UserRepositoryImpl._ROLE_PRIORITY:
            if candidate in role_set:
                try:
                    return UserRole(candidate)
                except ValueError:
                    continue
        # Fallback: first role or default
        try:
            return UserRole(model.roles[0].role)
        except ValueError:
            return UserRole.FARMER_SINGLE

    @staticmethod
    def _all_roles_from_model(model: UserModel) -> list[UserRole]:
        """Extract all roles from the eagerly loaded roles relationship."""
        roles: list[UserRole] = []
        for r in model.roles:
            try:
                roles.append(UserRole(r.role))
            except ValueError:
                continue
        return roles or [UserRole.FARMER_SINGLE]

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
        await self._session.flush()

    async def find_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        model = await self._session.get(UserModel, user_id)
        if not model:
            return None
        role = self._primary_role_from_model(model)
        return self._to_entity(model, role)

    async def find_by_phone_number(self, phone_number: str) -> Optional[User]:
        result = await self._session.execute(select(UserModel).where(UserModel.phone == phone_number))
        model = result.scalar_one_or_none()
        if not model:
            return None
        role = self._primary_role_from_model(model)
        return self._to_entity(model, role)

    async def list_by_role(self, role: UserRole) -> List[User]:
        result = await self._session.execute(
            select(UserModel)
            .join(UserRoleModel, UserRoleModel.user_id == UserModel.user_id)
            .where(UserRoleModel.role == role.value)
        )
        return [self._to_entity(m, role) for m in result.scalars().all()]

    async def list_by_province(self, province: str) -> List[User]:
        result = await self._session.execute(select(UserModel).where(UserModel.province == province))
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_coop_id(self, coop_id: uuid.UUID) -> List[User]:
        return []  # MVP: coop support deferred

    async def delete(self, user_id: uuid.UUID) -> None:
        await self._session.execute(sa_delete(UserModel).where(UserModel.user_id == user_id))
        await self._session.flush()
