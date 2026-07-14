# Permission Engine — user role repository.

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.role import Role
from database.models.user_role import UserRole
from database.models.users import User


class UserRoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _resolve_user_id(self, user_id: int | uuid.UUID) -> uuid.UUID | None:
        if isinstance(user_id, uuid.UUID):
            return user_id
        result = await self._session.execute(
            select(User.id).where(User.telegram_id == user_id)
        )
        return result.scalar_one_or_none()

    async def assign_role(self, user_id: int | uuid.UUID, role_id: uuid.UUID) -> UserRole | None:
        resolved_user_id = await self._resolve_user_id(user_id)
        if resolved_user_id is None:
            return None

        existing = await self._session.execute(
            select(UserRole).where(
                UserRole.user_id == resolved_user_id,
                UserRole.role_id == role_id,
            )
        )
        link = existing.scalar_one_or_none()
        if link is not None:
            return link

        link = UserRole(user_id=resolved_user_id, role_id=role_id)
        self._session.add(link)
        await self._session.flush()
        return link

    async def remove_role(self, user_id: int | uuid.UUID, role_id: uuid.UUID) -> bool:
        resolved_user_id = await self._resolve_user_id(user_id)
        if resolved_user_id is None:
            return False

        result = await self._session.execute(
            delete(UserRole).where(
                UserRole.user_id == resolved_user_id,
                UserRole.role_id == role_id,
            )
        )
        await self._session.flush()
        return result.rowcount > 0

    async def get_user_roles(self, user_id: int | uuid.UUID) -> list[Role]:
        resolved_user_id = await self._resolve_user_id(user_id)
        if resolved_user_id is None:
            return []

        result = await self._session.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == resolved_user_id)
            .order_by(Role.code.asc())
        )
        return list(result.scalars().all())

    async def get_role_by_code(self, role_code: str) -> Role | None:
        result = await self._session.execute(
            select(Role).where(Role.code == role_code)
        )
        return result.scalar_one_or_none()

    async def find_user_by_role_code(self, role_code: str) -> User | None:
        result = await self._session.execute(
            select(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(Role.code == role_code)
            .order_by(User.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def assign_role_by_code(
        self,
        user_id: int | uuid.UUID,
        role_code: str,
    ) -> UserRole | None:
        role = await self.get_role_by_code(role_code)
        if role is None:
            return None
        return await self.assign_role(user_id, role.id)
