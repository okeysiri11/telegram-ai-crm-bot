# Platform Memory — session memory repository.

from __future__ import annotations

from platform_memory.exceptions import MemoryValidationError
from platform_memory.models import SessionMemoryRecord, new_id
from platform_memory.providers.base import SessionMemoryProvider


class SessionMemoryRepository:
    __slots__ = ("_provider",)

    def __init__(self, provider: SessionMemoryProvider) -> None:
        self._provider = provider

    async def remember(
        self,
        *,
        session_id: str,
        content: str,
        memory_key: str = "",
        user_id: str | None = None,
        agent_id: str | None = None,
        expires_at: str | None = None,
        metadata: dict | None = None,
    ) -> SessionMemoryRecord:
        if not session_id:
            raise MemoryValidationError("session_id is required")
        record = SessionMemoryRecord(
            memory_id=new_id(),
            session_id=session_id,
            content=content,
            memory_key=memory_key,
            user_id=user_id,
            agent_id=agent_id,
            expires_at=expires_at,
            metadata=dict(metadata or {}),
        )
        return await self._provider.save(record)

    async def list_memory(
        self,
        *,
        session_id: str | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[SessionMemoryRecord]:
        return await self._provider.list_records(session_id=session_id, user_id=user_id, limit=limit)
