"""Epic 45.2 — Search Everywhere across memory layers + semantic RAG."""

from __future__ import annotations

from typing import Any

from platform_memory.continuity_store import continuity_store
from platform_memory.memory_embeddings import memory_embeddings
from platform_memory.memory_permissions import MemoryPrincipal, filter_readable


SEARCH_SCOPES = (
    "crm",
    "erp",
    "knowledge",
    "documents",
    "memory",
    "history",
    "projects",
    "ai_studio",
    "telegram",
    "workflow",
    "agents",
)


class MemorySearch:
    """Unified search: lexical + semantic over continuous memory."""

    def search(
        self,
        principal: MemoryPrincipal,
        query: str,
        *,
        scopes: list[str] | None = None,
        limit: int = 30,
    ) -> dict[str, Any]:
        q = (query or "").strip().lower()
        scopes = scopes or list(SEARCH_SCOPES)
        records = filter_readable(
            principal,
            continuity_store.list_for(principal.owner_id, company_id=principal.company_id, limit=500),
        )
        hits: list[dict[str, Any]] = []
        for r in records:
            blob = f"{r.title} {r.content} {' '.join(r.tags)} {r.kind} {r.level}".lower()
            lexical = 1.0 if q and q in blob else 0.0
            if not q:
                lexical = 0.1
            # scope hint via tags/kind/channel
            scope_hit = any(s in r.tags or s in r.kind or s == r.channel for s in scopes)
            if q and lexical == 0.0 and not any(tok in blob for tok in q.split()):
                continue
            semantic = memory_embeddings.similarity(
                memory_embeddings.embed(query),
                r.embedding or memory_embeddings.embed(f"{r.title} {r.content}"),
            )
            score = max(lexical, semantic) + (0.05 if scope_hit else 0.0) + (0.1 if r.pinned else 0.0)
            if score <= 0:
                continue
            hits.append({**r.to_dict(), "score": round(score, 4), "scopes": scopes})
        hits.sort(key=lambda x: x["score"], reverse=True)
        return {
            "query": query,
            "scopes": scopes,
            "count": len(hits[:limit]),
            "results": hits[:limit],
        }

    def search_knowledge(self, principal: MemoryPrincipal, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
        knowledge = [
            r
            for r in continuity_store.list_for(
                principal.owner_id, company_id=principal.company_id, limit=300, principal=principal
            )
            if r.level in ("knowledge", "long_term", "project")
        ]
        docs = [(r.id, f"{r.title}\n{r.content}") for r in knowledge]
        ranked = memory_embeddings.rank(query, docs)[:limit]
        by_id = {r.id: r for r in knowledge}
        return [{**by_id[i].to_dict(), "score": s} for i, s in ranked if i in by_id]


memory_search = MemorySearch()
