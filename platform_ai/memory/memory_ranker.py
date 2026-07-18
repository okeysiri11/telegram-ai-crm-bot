# Result re-ranking for retrieval quality.

from __future__ import annotations

import re
from typing import Any

from platform_ai.memory.models import SearchResult


class MemoryRanker:
    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        *,
        boost_recent: bool = True,
        context_filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        if not results:
            return []
        query_terms = set(re.findall(r"\w+", query.lower()))
        context_filters = context_filters or {}

        scored: list[tuple[float, SearchResult]] = []
        for result in results:
            score = result.score
            content_lower = result.content.lower()
            term_hits = sum(1 for t in query_terms if t in content_lower)
            if query_terms:
                score += term_hits / len(query_terms) * 0.3
            if context_filters.get("plugin_id") and result.metadata.get("plugin_id") == context_filters["plugin_id"]:
                score += 0.1
            if context_filters.get("memory_type") and result.metadata.get("memory_type") == context_filters["memory_type"]:
                score += 0.05
            if boost_recent and result.metadata.get("updated_at"):
                score += 0.02
            scored.append((score, result))

        scored.sort(key=lambda x: x[0], reverse=True)
        ranked: list[SearchResult] = []
        for score, result in scored:
            result.score = round(score, 4)
            ranked.append(result)
        return ranked


memory_ranker = MemoryRanker()
