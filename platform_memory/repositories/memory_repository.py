# Platform Memory — abstract semantic memory repository.

from __future__ import annotations

from abc import ABC, abstractmethod

from platform_memory.entities import MemoryEntity, MemoryFilters


class MemoryRepository(ABC):
    """Persistence contract — no SQL in services."""

    @abstractmethod
    async def save(self, entity: MemoryEntity) -> MemoryEntity:
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: MemoryEntity) -> MemoryEntity:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get(self, memory_id: str) -> MemoryEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: str, *, filters: MemoryFilters | None = None, limit: int = 20) -> list[MemoryEntity]:
        raise NotImplementedError

    @abstractmethod
    async def search_by_embedding(
        self,
        embedding: list[float],
        *,
        filters: MemoryFilters | None = None,
        limit: int = 20,
        similarity_threshold: float = 0.0,
    ) -> list[tuple[MemoryEntity, float]]:
        raise NotImplementedError

    @abstractmethod
    async def recent(self, *, filters: MemoryFilters | None = None, limit: int = 20) -> list[MemoryEntity]:
        raise NotImplementedError

    @abstractmethod
    async def important(self, *, filters: MemoryFilters | None = None, limit: int = 20) -> list[MemoryEntity]:
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError
