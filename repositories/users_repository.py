# Users repository — PostgreSQL async data access.

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.users import User


class UsersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def ensure_user(
        self,
        *,
        telegram_id: int,
        username: str | None = None,
        full_name: str | None = None,
        is_active: bool = True,
    ) -> User:
        row = await self.get_by_telegram_id(telegram_id)
        if row is not None:
            changed = False
            if username and row.username != username:
                row.username = username
                changed = True
            if full_name and row.full_name != full_name:
                row.full_name = full_name
                changed = True
            if not row.is_active and is_active:
                row.is_active = True
                changed = True
            if changed:
                await self._session.flush()
            return row

        row = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            is_active=is_active,
        )
        self._session.add(row)
        await self._session.flush()
        return row
