# Platform Memory — project memory repository.

from __future__ import annotations

from platform_memory.exceptions import MemoryValidationError
from platform_memory.models import ProjectMemoryRecord, new_id
from platform_memory.providers.base import ProjectMemoryProvider


class ProjectMemoryRepository:
    __slots__ = ("_provider",)

    def __init__(self, provider: ProjectMemoryProvider) -> None:
        self._provider = provider

    async def remember(
        self,
        *,
        project_id: str,
        content: str,
        memory_key: str = "",
        metadata: dict | None = None,
    ) -> ProjectMemoryRecord:
        if not project_id:
            raise MemoryValidationError("project_id is required")
        record = ProjectMemoryRecord(
            memory_id=new_id(),
            project_id=project_id,
            content=content,
            memory_key=memory_key,
            metadata=dict(metadata or {}),
        )
        return await self._provider.save(record)

    async def list_memory(self, project_id: str, *, limit: int = 100) -> list[ProjectMemoryRecord]:
        return await self._provider.list_records(project_id, limit=limit)
