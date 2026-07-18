# Knowledge-specific search API.

from __future__ import annotations

import time
from typing import Any

from platform_ai.memory.memory_retriever import memory_retriever
from platform_ai.memory.models import SearchMode, SearchResult


class KnowledgeSearch:
    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        plugin_id: str | None = None,
        provider_id: str | None = None,
        mode: str = SearchMode.HYBRID.value,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        all_results = await memory_retriever.search(
            query,
            mode=mode,
            limit=limit * 2,
            plugin_id=plugin_id,
            provider_id=provider_id,
        )
        knowledge = [r for r in all_results if r.source_type == "knowledge"][:limit]
        latency_ms = (time.perf_counter() - start) * 1000
        return {
            "query": query,
            "results": [r.to_dict() for r in knowledge],
            "count": len(knowledge),
            "latency_ms": round(latency_ms, 2),
        }


knowledge_search = KnowledgeSearch()
