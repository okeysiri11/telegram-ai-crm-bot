# Memory & knowledge retrieval — semantic, keyword, hybrid search.

from __future__ import annotations

import re
import time
from typing import Any
from uuid import uuid4

from platform_ai.memory.memory_embeddings import cosine_similarity, embedding_registry
from platform_ai.memory.memory_ranker import memory_ranker
from platform_ai.memory.memory_store import memory_store
from platform_ai.memory.models import SearchMode, SearchResult
from platform_ai.memory.knowledge_index import knowledge_index


class MemoryRetriever:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, list[SearchResult]]] = {}
        self._cache_ttl = 300.0
        self._last_latency_ms = 0.0

    def reset(self) -> None:
        self._cache.clear()
        self._last_latency_ms = 0.0

    @property
    def last_latency_ms(self) -> float:
        return self._last_latency_ms

    async def search(
        self,
        query: str,
        *,
        mode: str = SearchMode.HYBRID.value,
        limit: int = 10,
        plugin_id: str | None = None,
        user_id: str | None = None,
        memory_type: str | None = None,
        provider_id: str | None = None,
        use_cache: bool = True,
        context_filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        start = time.perf_counter()
        cache_key = f"{mode}:{query}:{plugin_id}:{user_id}:{memory_type}:{limit}"
        if use_cache and cache_key in self._cache:
            expires, cached = self._cache[cache_key]
            if time.time() < expires:
                self._last_latency_ms = (time.perf_counter() - start) * 1000
                return cached[:limit]

        filters: dict[str, Any] = {}
        if plugin_id:
            filters["plugin_id"] = plugin_id
        if user_id:
            filters["user_id"] = user_id
        if memory_type:
            filters["memory_type"] = memory_type

        memory_results = self._search_memory(query, mode, filters, provider_id)
        knowledge_results = await self._search_knowledge(query, mode, filters, provider_id)
        combined = memory_results + knowledge_results

        ctx_filters = dict(context_filters or {})
        ctx_filters.update({k: v for k, v in filters.items() if v})
        ranked = memory_ranker.rerank(query, combined, context_filters=ctx_filters)

        self._cache[cache_key] = (time.time() + self._cache_ttl, ranked)
        self._last_latency_ms = (time.perf_counter() - start) * 1000
        return ranked[:limit]

    def _search_memory(
        self,
        query: str,
        mode: str,
        filters: dict[str, Any],
        provider_id: str | None,
    ) -> list[SearchResult]:
        records = memory_store.list_all(**filters)
        results: list[SearchResult] = []
        query_lower = query.lower()
        query_terms = set(re.findall(r"\w+", query_lower))

        query_emb: list[float] | None = None
        if mode in (SearchMode.SEMANTIC.value, SearchMode.HYBRID.value):
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    query_emb = None
                else:
                    query_emb = loop.run_until_complete(embedding_registry.get(provider_id).embed(query))
            except Exception:
                query_emb = None

        for record in records:
            score = 0.0
            if mode in (SearchMode.KEYWORD.value, SearchMode.HYBRID.value):
                content_lower = record.content.lower()
                hits = sum(1 for t in query_terms if t in content_lower)
                if query_terms:
                    score = hits / len(query_terms)
                if query_lower in content_lower:
                    score = max(score, 0.9)
            if mode == SearchMode.SEMANTIC.value and query_emb:
                record_emb = _text_embed(record.content)
                score = cosine_similarity(query_emb, record_emb)
            if score > 0:
                results.append(
                    SearchResult(
                        result_id=str(uuid4()),
                        source_type="memory",
                        content=record.content,
                        score=score,
                        memory_id=record.memory_id,
                        metadata={
                            "memory_type": record.memory_type,
                            "key": record.key,
                            "plugin_id": record.plugin_id,
                            "user_id": record.user_id,
                            "updated_at": record.updated_at,
                        },
                    )
                )
        return results

    async def _search_knowledge(
        self,
        query: str,
        mode: str,
        filters: dict[str, Any],
        provider_id: str | None,
    ) -> list[SearchResult]:
        chunks = knowledge_index.get_chunks()
        if plugin_id := filters.get("plugin_id"):
            from platform_ai.memory.document_store import document_store

            doc_ids = {d.document_id for d in document_store.list_all(plugin_id=plugin_id)}
            chunks = [c for c in chunks if c.document_id in doc_ids]

        results: list[SearchResult] = []
        query_lower = query.lower()
        query_terms = set(re.findall(r"\w+", query_lower))
        query_emb: list[float] | None = None
        if mode in (SearchMode.SEMANTIC.value, SearchMode.HYBRID.value):
            query_emb = await embedding_registry.get(provider_id).embed(query)

        for chunk in chunks:
            score = 0.0
            if mode in (SearchMode.KEYWORD.value, SearchMode.HYBRID.value):
                content_lower = chunk.content.lower()
                hits = sum(1 for t in query_terms if t in content_lower)
                if query_terms:
                    score = hits / len(query_terms)
            if mode in (SearchMode.SEMANTIC.value, SearchMode.HYBRID.value) and query_emb and chunk.embedding:
                sem_score = cosine_similarity(query_emb, chunk.embedding)
                score = (score + sem_score) / 2 if mode == SearchMode.HYBRID.value else sem_score
            elif mode == SearchMode.SEMANTIC.value and query_emb:
                sem_score = cosine_similarity(query_emb, chunk.embedding or _text_embed(chunk.content))
                score = sem_score
            if score > 0.01:
                results.append(
                    SearchResult(
                        result_id=str(uuid4()),
                        source_type="knowledge",
                        content=chunk.content,
                        score=score,
                        document_id=chunk.document_id,
                        chunk_id=chunk.chunk_id,
                        metadata=dict(chunk.metadata),
                    )
                )
        return results

    def invalidate_cache(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count


def _text_embed(text: str) -> list[float]:
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            from platform_ai.memory.memory_embeddings import _hash_embed

            return _hash_embed(f"local:{text}", 384)
        return loop.run_until_complete(embedding_registry.get("local").embed(text))
    except Exception:
        from platform_ai.memory.memory_embeddings import _hash_embed

        return _hash_embed(f"local:{text}", 384)


memory_retriever = MemoryRetriever()
