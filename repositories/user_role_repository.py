# Permission Engine — user role repository.

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.role import Role
from database.models.user_role import UserRole


class UserRoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def assign_role(self, user_id: int, role_id: uuid.UUID) -> UserRole:
        existing = await self._session.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )
        link = existing.scalar_one_or_none()
        if link is not None:
            return link

        link = UserRole(user_id=user_id, role_id=role_id)
        self._session.add(link)
        await self._session.flush()
        return link

    async def remove_role(self, user_id: int, role_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            delete(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )
        await self._session.flush()
        return result.rowcount > 0

    async def get_user_roles(self, user_id: int) -> list[Role]:
        result = await self._session.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
            .order_by(Role.code.asc())
        )
        return list(result.scalars().all())
