# Platform Memory — business facts repository.

from __future__ import annotations

from platform_memory.exceptions import MemoryValidationError
from platform_memory.models import BusinessFact, new_id
from platform_memory.providers.base import BusinessMemoryProvider


class BusinessMemoryRepository:
    __slots__ = ("_provider",)

    def __init__(self, provider: BusinessMemoryProvider) -> None:
        self._provider = provider

    async def remember_fact(
        self,
        *,
        organization_id: str,
        key: str,
        value: str,
        metadata: dict | None = None,
    ) -> BusinessFact:
        if not organization_id or not key:
            raise MemoryValidationError("organization_id and key are required")
        fact = BusinessFact(
            fact_id=new_id(),
            organization_id=organization_id,
            key=key,
            value=value,
            metadata=dict(metadata or {}),
        )
        return await self._provider.upsert_fact(fact)

    async def list_facts(self, organization_id: str, *, limit: int = 100) -> list[BusinessFact]:
        return await self._provider.list_facts(organization_id, limit=limit)
