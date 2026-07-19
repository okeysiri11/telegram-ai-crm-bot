# Platform Memory — user profile repository.

from __future__ import annotations

from platform_memory.exceptions import MemoryValidationError
from platform_memory.models import UserFact, new_id
from platform_memory.providers.base import UserProfileProvider


class UserProfileRepository:
    __slots__ = ("_provider",)

    def __init__(self, provider: UserProfileProvider) -> None:
        self._provider = provider

    async def remember_fact(
        self,
        *,
        user_id: str,
        key: str,
        value: str,
        source: str = "explicit",
        metadata: dict | None = None,
    ) -> UserFact:
        if not user_id or not key:
            raise MemoryValidationError("user_id and key are required")
        fact = UserFact(
            fact_id=new_id(),
            user_id=user_id,
            key=key,
            value=value,
            source=source,
            metadata=dict(metadata or {}),
        )
        return await self._provider.upsert_fact(fact)

    async def get_fact(self, user_id: str, key: str) -> UserFact | None:
        return await self._provider.get_fact(user_id, key)

    async def list_facts(self, user_id: str, *, limit: int = 100) -> list[UserFact]:
        return await self._provider.list_facts(user_id, limit=limit)

    async def forget_fact(self, user_id: str, key: str) -> bool:
        return await self._provider.delete_fact(user_id, key)
