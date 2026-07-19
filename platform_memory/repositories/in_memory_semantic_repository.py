# Platform Memory — in-memory semantic memory repository.

from __future__ import annotations

import re
from datetime import datetime, timezone

from platform_memory.entities import MemoryEntity, MemoryFilters
from platform_memory.providers.embedding_provider import cosine_similarity
from platform_memory.repositories.memory_repository import MemoryRepository


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t}


def _matches_filters(entity: MemoryEntity, filters: MemoryFilters | None) -> bool:
    if filters is None:
        return True
    if filters.owner_id is not None and entity.owner_id != filters.owner_id:
        return False
    if filters.agent_id is not None and entity.agent_id != filters.agent_id:
        return False
    if filters.session_id is not None and entity.session_id != filters.session_id:
        return False
    return True


def _is_expired(entity: MemoryEntity) -> bool:
    if not entity.expires_at:
        return False
    try:
        expires = datetime.fromisoformat(entity.expires_at)
        return expires <= datetime.now(timezone.utc)
    except ValueError:
        return False


class InMemoryMemoryRepository(MemoryRepository):
    """Default in-memory store — swappable with pgvector/Qdrant/Milvus/Weaviate adapters."""

    def __init__(self) -> None:
        self._store: dict[str, MemoryEntity] = {}

    async def save(self, entity: MemoryEntity) -> MemoryEntity:
        self._store[entity.id] = entity
        return entity

    async def update(self, entity: MemoryEntity) -> MemoryEntity:
        if entity.id not in self._store:
            raise KeyError(f"Memory not found: {entity.id}")
        updated = MemoryEntity(
            id=entity.id,
            owner_id=entity.owner_id,
            agent_id=entity.agent_id,
            session_id=entity.session_id,
            text=entity.text,
            summary=entity.summary,
            embedding=list(entity.embedding),
            importance_score=entity.importance_score,
            created_at=self._store[entity.id].created_at,
            updated_at=datetime.now(timezone.utc).isoformat(),
            expires_at=entity.expires_at,
            metadata=dict(entity.metadata),
        )
        self._store[entity.id] = updated
        return updated

    async def delete(self, memory_id: str) -> bool:
        return self._store.pop(memory_id, None) is not None

    async def get(self, memory_id: str) -> MemoryEntity | None:
        entity = self._store.get(memory_id)
        if entity and _is_expired(entity):
            await self.delete(memory_id)
            return None
        return entity

    async def _active(self, filters: MemoryFilters | None) -> list[MemoryEntity]:
        active: list[MemoryEntity] = []
        for entity in self._store.values():
            if _is_expired(entity):
                continue
            if _matches_filters(entity, filters):
                active.append(entity)
        return active

    async def search(
        self,
        query: str,
        *,
        filters: MemoryFilters | None = None,
        limit: int = 20,
    ) -> list[MemoryEntity]:
        tokens = _tokenize(query)
        if not tokens:
            return (await self.recent(filters=filters, limit=limit))[:limit]

        scored: list[tuple[float, MemoryEntity]] = []
        for entity in await self._active(filters):
            haystack = _tokenize(entity.text + " " + (entity.summary or ""))
            if not haystack:
                continue
            overlap = len(tokens & haystack) / max(len(tokens), 1)
            if overlap > 0:
                scored.append((overlap, entity))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [entity for _, entity in scored[:limit]]

    async def search_by_embedding(
        self,
        embedding: list[float],
        *,
        filters: MemoryFilters | None = None,
        limit: int = 20,
        similarity_threshold: float = 0.0,
    ) -> list[tuple[MemoryEntity, float]]:
        scored: list[tuple[MemoryEntity, float]] = []
        for entity in await self._active(filters):
            if not entity.embedding:
                continue
            similarity = cosine_similarity(embedding, entity.embedding)
            if similarity >= similarity_threshold:
                scored.append((entity, similarity))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]

    async def recent(self, *, filters: MemoryFilters | None = None, limit: int = 20) -> list[MemoryEntity]:
        entities = await self._active(filters)
        entities.sort(key=lambda e: e.updated_at, reverse=True)
        return entities[:limit]

    async def important(self, *, filters: MemoryFilters | None = None, limit: int = 20) -> list[MemoryEntity]:
        entities = await self._active(filters)
        entities.sort(key=lambda e: e.importance_score, reverse=True)
        return entities[:limit]

    async def clear(self) -> None:
        self._store.clear()
