# User repository — PostgreSQL data access (no business rules).

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.users import User
from repositories.user_role_repository import UserRoleRepository
from src.platform.layers.base_repository import BaseRepository

# Backward-compatible alias for existing imports.
from repositories.users_repository import UsersRepository as _UsersRepository


class UserRepository(BaseRepository):
    """Unified user persistence facade."""

    def _users(self) -> _UsersRepository:
        return _UsersRepository(self.session)

    def _roles(self) -> UserRoleRepository:
        return UserRoleRepository(self.session)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self._users().get_by_telegram_id(telegram_id)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._users().get_by_id(user_id)

    async def ensure_user(
        self,
        *,
        telegram_id: int,
        username: str | None = None,
        full_name: str | None = None,
        is_active: bool = True,
    ) -> User:
        return await self._users().ensure_user(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            is_active=is_active,
        )

    async def update_profile(
        self,
        user: User,
        *,
        username: str | None = None,
        full_name: str | None = None,
        role: str | None = None,
        verticals: list[str] | None = None,
    ) -> User:
        if username is not None:
            user.username = username
        if full_name is not None:
            user.full_name = full_name
        if role is not None:
            user.role = role
        if verticals is not None:
            user.verticals = verticals
        await self.session.flush()
        return user

    async def list_role_codes(self, user_id: uuid.UUID) -> list[str]:
        roles = await self._roles().get_user_roles(user_id)
        return [r.code for r in roles]

    async def assign_role_by_code(self, user_id: uuid.UUID, role_code: str) -> None:
        await self._roles().assign_role_by_code(user_id, role_code)

    async def find_by_role_code(self, role_code: str) -> User | None:
        return await self._roles().find_user_by_role_code(role_code)

    @staticmethod
    def snapshot(user: User) -> dict[str, Any]:
        return {
            "id": str(user.id),
            "telegram_id": user.telegram_id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "verticals": list(user.verticals or []),
            "is_active": user.is_active,
        }
