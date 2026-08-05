"""User memory repository — PostgreSQL key/value profile facts."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user_memory import UserMemory
from src.platform.layers.base_repository import BaseRepository


class UserMemoryRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_by_telegram(self, telegram_id: int) -> list[UserMemory]:
        result = await self.session.execute(
            select(UserMemory).where(UserMemory.telegram_id == telegram_id)
        )
        return list(result.scalars().all())

    async def get(self, telegram_id: int, key: str) -> UserMemory | None:
        result = await self.session.execute(
            select(UserMemory).where(
                UserMemory.telegram_id == telegram_id,
                UserMemory.memory_key == key,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, telegram_id: int, key: str, value: str) -> UserMemory:
        row = await self.get(telegram_id, key)
        if row is None:
            row = UserMemory(telegram_id=telegram_id, memory_key=key, memory_value=value)
            self.session.add(row)
        else:
            row.memory_value = value
        await self.session.flush()
        return row
