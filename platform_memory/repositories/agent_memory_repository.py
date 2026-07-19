# Platform Memory — agent memory repository.

from __future__ import annotations

from platform_memory.exceptions import MemoryNotFoundError, MemoryValidationError
from platform_memory.models import AgentMemoryRecord, MemoryCategory, new_id
from platform_memory.providers.base import AgentMemoryProvider


class AgentMemoryRepository:
    __slots__ = ("_provider",)

    def __init__(self, provider: AgentMemoryProvider) -> None:
        self._provider = provider

    async def remember(
        self,
        *,
        agent_id: str,
        content: str,
        memory_key: str = "",
        user_id: str | None = None,
        session_id: str | None = None,
        category: str = MemoryCategory.AGENT.value,
        metadata: dict | None = None,
        memory_id: str | None = None,
    ) -> AgentMemoryRecord:
        if not agent_id:
            raise MemoryValidationError("agent_id is required")
        if not content.strip():
            raise MemoryValidationError("content must not be empty")

        if memory_key:
            existing = await self._provider.get_by_key(
                agent_id,
                memory_key,
                user_id=user_id,
                session_id=session_id,
            )
            if existing:
                updated = AgentMemoryRecord(
                    memory_id=existing.memory_id,
                    agent_id=agent_id,
                    content=content,
                    memory_key=memory_key,
                    user_id=user_id,
                    session_id=session_id,
                    category=category,
                    metadata={**existing.metadata, **(metadata or {})},
                    created_at=existing.created_at,
                )
                return await self._provider.save(updated)

        record = AgentMemoryRecord(
            memory_id=memory_id or new_id(),
            agent_id=agent_id,
            content=content,
            memory_key=memory_key,
            user_id=user_id,
            session_id=session_id,
            category=category,
            metadata=dict(metadata or {}),
        )
        return await self._provider.save(record)

    async def recall(self, memory_id: str) -> AgentMemoryRecord:
        record = await self._provider.get(memory_id)
        if record is None:
            raise MemoryNotFoundError(memory_id)
        return record

    async def recall_by_key(
        self,
        agent_id: str,
        memory_key: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> AgentMemoryRecord:
        record = await self._provider.get_by_key(agent_id, memory_key, user_id=user_id, session_id=session_id)
        if record is None:
            raise MemoryNotFoundError(memory_key)
        return record

    async def list_memory(
        self,
        *,
        agent_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> list[AgentMemoryRecord]:
        return await self._provider.list_records(
            agent_id=agent_id,
            user_id=user_id,
            session_id=session_id,
            category=category,
            limit=limit,
        )

    async def forget(self, memory_id: str) -> bool:
        return await self._provider.delete(memory_id)
