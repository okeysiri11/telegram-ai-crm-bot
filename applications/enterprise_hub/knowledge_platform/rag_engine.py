"""RAG engine — retrieval, expansion, multi-doc, re-rank, citation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.knowledge_platform.citation import CitationEngine
from applications.enterprise_hub.knowledge_platform.retrieval import RetrievalEngine
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class RAGEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.retrieval = RetrievalEngine(self.store)
        self.citations = CitationEngine(self.store)

    def answer(
        self,
        *,
        query: str,
        mode: str = "hybrid",
        top_k: int = 5,
        expand: bool = True,
    ) -> dict[str, Any]:
        retrieved = self.retrieval.retrieve(query=query, mode=mode, top_k=top_k, expand=expand)
        hits = retrieved.get("hits") or []
        context = "\n---\n".join(h.get("text", "") for h in hits if h.get("text"))
        answer_text = f"Based on {len(hits)} sources: {query}"
        if hits:
            answer_text = f"{answer_text}\n\nKey excerpts:\n{context[:500]}"
        aid = _id("ekp_ans")
        citation = self.citations.cite(answer_id=aid, hits=hits)
        return self.store.ekp_answers.save(
            aid,
            {
                "answer_id": aid,
                "query": query,
                "retrieval_id": retrieved["retrieval_id"],
                "citation_id": citation["citation_id"],
                "answer": answer_text,
                "sources": citation["sources"],
                "mode": mode,
                "at": _now(),
            },
        )
