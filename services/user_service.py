# UserService — user lifecycle, roles, verticals, access checks.

from __future__ import annotations

import uuid
from typing import Any

from database.session import get_session
from repositories.user_repository import UserRepository
from services.system_roles import SystemRole, normalize_vertical


class UserService:
    """PostgreSQL-only user operations."""

    @staticmethod
    async def get_user(*, telegram_id: int) -> dict[str, Any] | None:
        async with get_session() as session:
            user = await UserRepository(session).get_by_telegram_id(telegram_id)
            if user is None:
                return None
            return UserRepository.snapshot(user)

    @staticmethod
    async def get_user_by_id(user_id: uuid.UUID | str) -> dict[str, Any] | None:
        uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        async with get_session() as session:
            user = await UserRepository(session).get_by_id(uid)
            if user is None:
                return None
            return UserRepository.snapshot(user)

    @staticmethod
    async def ensure_user(
        *,
        telegram_id: int,
        full_name: str = "",
        username: str = "",
        is_active: bool = True,
    ) -> dict[str, Any]:
        async with get_session() as session:
            repo = UserRepository(session)
            user = await repo.ensure_user(
                telegram_id=telegram_id,
                username=username or None,
                full_name=full_name or None,
                is_active=is_active,
            )
            return UserRepository.snapshot(user)

    @staticmethod
    async def update_profile(
        *,
        telegram_id: int,
        username: str | None = None,
        full_name: str | None = None,
    ) -> dict[str, Any] | None:
        async with get_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_telegram_id(telegram_id)
            if user is None:
                return None
            await repo.update_profile(user, username=username, full_name=full_name)
            return UserRepository.snapshot(user)

    @staticmethod
    async def assign_role(*, telegram_id: int, role_code: str) -> dict[str, Any] | None:
        async with get_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_telegram_id(telegram_id)
            if user is None:
                return None
            await repo.assign_role_by_code(user.id, role_code)
            await repo.update_profile(user, role=role_code)
            return UserRepository.snapshot(user)

    @staticmethod
    async def assign_verticals(
        *,
        telegram_id: int,
        verticals: list[str],
    ) -> dict[str, Any] | None:
        normalized = [normalize_vertical(v) or v for v in verticals]
        async with get_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_telegram_id(telegram_id)
            if user is None:
                return None
            await repo.update_profile(user, verticals=normalized)
            return UserRepository.snapshot(user)

    @staticmethod
    async def check_access(
        *,
        telegram_id: int,
        permission: str,
    ) -> bool:
        from services.role_service import role_service

        return await role_service.has_permission(telegram_id, permission)

    @staticmethod
    async def list_roles(*, telegram_id: int) -> list[str]:
        async with get_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_telegram_id(telegram_id)
            if user is None:
                return []
            return await repo.list_role_codes(user.id)


user_service = UserService()
