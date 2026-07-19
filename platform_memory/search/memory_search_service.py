# Platform Memory — semantic search service.

from __future__ import annotations

import re
from datetime import datetime, timezone

from platform_memory.config import DEFAULT_SEMANTIC_CONFIG, SemanticMemoryConfig
from platform_memory.entities import MemoryEntity, MemoryFilters, MemorySearchHit
from platform_memory.providers.embedding_provider import EmbeddingProvider
from platform_memory.repositories.memory_repository import MemoryRepository


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t}


def _keyword_score(query: str, entity: MemoryEntity) -> float:
    tokens = _tokenize(query)
    if not tokens:
        return 0.0
    haystack = _tokenize(entity.text + " " + (entity.summary or ""))
    if not haystack:
        return 0.0
    return len(tokens & haystack) / len(tokens)


def _recency_score(entity: MemoryEntity) -> float:
    try:
        updated = datetime.fromisoformat(entity.updated_at)
        age_hours = max((datetime.now(timezone.utc) - updated).total_seconds() / 3600, 0.0)
    except ValueError:
        return 0.0
    return 1.0 / (1.0 + age_hours)


class MemorySearchService:
    """Semantic search with keyword fallback, ranking, and boost factors."""

    __slots__ = ("_repository", "_embedding", "_config")

    def __init__(
        self,
        *,
        repository: MemoryRepository,
        embedding: EmbeddingProvider,
        config: SemanticMemoryConfig | None = None,
    ) -> None:
        self._repository = repository
        self._embedding = embedding
        self._config = config or DEFAULT_SEMANTIC_CONFIG
        self._config.validate()

    @property
    def config(self) -> SemanticMemoryConfig:
        return self._config

    async def search(
        self,
        query: str,
        *,
        filters: MemoryFilters | None = None,
        limit: int | None = None,
    ) -> list[MemorySearchHit]:
        limit = limit or self._config.max_memories
        query = query.strip()
        if not query:
            recent = await self._repository.recent(filters=filters, limit=limit)
            return [self._rank_entity(entity, semantic=0.0, keyword=0.0) for entity in recent]

        query_embedding = await self._embedding.embed(query)
        semantic_hits = await self._repository.search_by_embedding(
            query_embedding,
            filters=filters,
            limit=limit * 2,
            similarity_threshold=self._config.similarity_threshold,
        )

        hits: dict[str, MemorySearchHit] = {}
        for entity, similarity in semantic_hits:
            keyword = _keyword_score(query, entity)
            hits[entity.id] = self._rank_entity(entity, semantic=similarity, keyword=keyword)

        if not hits:
            keyword_entities = await self._repository.search(query, filters=filters, limit=limit)
            for entity in keyword_entities:
                keyword = _keyword_score(query, entity)
                if keyword >= self._config.keyword_fallback_min_score:
                    hits[entity.id] = self._rank_entity(entity, semantic=0.0, keyword=keyword)

        ranked = sorted(hits.values(), key=lambda hit: hit.score, reverse=True)
        return ranked[:limit]

    async def important(
        self,
        *,
        filters: MemoryFilters | None = None,
        limit: int | None = None,
    ) -> list[MemorySearchHit]:
        limit = limit or self._config.max_memories
        entities = await self._repository.important(filters=filters, limit=limit)
        return [self._rank_entity(entity, semantic=0.0, keyword=0.0) for entity in entities]

    async def recent(
        self,
        *,
        filters: MemoryFilters | None = None,
        limit: int | None = None,
    ) -> list[MemorySearchHit]:
        limit = limit or self._config.max_memories
        entities = await self._repository.recent(filters=filters, limit=limit)
        return [self._rank_entity(entity, semantic=0.0, keyword=0.0) for entity in entities]

    def _rank_entity(self, entity: MemoryEntity, *, semantic: float, keyword: float) -> MemorySearchHit:
        importance_boost = entity.importance_score * self._config.importance_weight
        recency_boost = _recency_score(entity) * self._config.recency_weight
        semantic_component = max(semantic, keyword) * max(
            0.0,
            1.0 - self._config.importance_weight - self._config.recency_weight,
        )
        final_score = semantic_component + importance_boost + recency_boost
        return MemorySearchHit(
            entity=entity,
            score=final_score,
            semantic_score=semantic,
            keyword_score=keyword,
            importance_boost=importance_boost,
            recency_boost=recency_boost,
        )
