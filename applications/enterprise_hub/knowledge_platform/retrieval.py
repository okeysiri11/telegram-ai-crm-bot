"""Retrieval — semantic / keyword / hybrid search over vector index."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.knowledge_platform.embedding_manager import EmbeddingManager, _embed
from applications.enterprise_hub.knowledge_platform.models import SEARCH_MODES
from applications.enterprise_hub.knowledge_platform.ranking import RankingEngine
from applications.enterprise_hub.knowledge_platform.vector_index import VectorIndex
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class RetrievalEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.vectors = VectorIndex(self.store)
        self.embeddings = EmbeddingManager(self.store)
        self.ranking = RankingEngine()

    def retrieve(
        self,
        *,
        query: str,
        mode: str = "hybrid",
        top_k: int = 5,
        expand: bool = False,
    ) -> dict[str, Any]:
        if not query:
            raise ValidationError("query is required")
        m = mode.lower().strip()
        if m not in SEARCH_MODES:
            raise ValidationError(f"mode must be one of {list(SEARCH_MODES)}")
        qvec = _embed(query)
        hits = []
        for v in self.vectors.all():
            sem = self.embeddings.cosine(qvec, v.get("vector") or [])
            text = (v.get("text") or "").lower()
            kw = 1.0 if any(t in text for t in query.lower().split()) else 0.0
            if m == "semantic":
                score = sem
            elif m == "keyword":
                score = kw
            elif m == "graph":
                score = sem * 0.7 + kw * 0.3
            else:
                score = 0.6 * sem + 0.4 * kw
            hits.append(
                {
                    "vector_id": v.get("vector_id"),
                    "chunk_id": v.get("chunk_id"),
                    "document_id": v.get("document_id"),
                    "text": v.get("text"),
                    "score": score,
                    "metadata": v.get("metadata") or {},
                }
            )
        hits = self.ranking.rerank(candidates=hits, query=query)[: max(1, top_k)]
        if expand and hits:
            doc_ids = {h["document_id"] for h in hits}
            for v in self.vectors.all():
                if v.get("document_id") in doc_ids and v.get("chunk_id") not in {h["chunk_id"] for h in hits}:
                    hits.append(
                        {
                            "vector_id": v.get("vector_id"),
                            "chunk_id": v.get("chunk_id"),
                            "document_id": v.get("document_id"),
                            "text": v.get("text"),
                            "score": 0.01,
                            "expanded": True,
                        }
                    )
                    if len(hits) >= top_k + 2:
                        break
        rid = _id("ekp_ret")
        return self.store.ekp_retrievals.save(
            rid,
            {
                "retrieval_id": rid,
                "query": query,
                "mode": m,
                "hits": hits[: top_k + (2 if expand else 0)],
                "at": _now(),
            },
        )
