"""Semantic search facade."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.knowledge_platform.retrieval import RetrievalEngine
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class SemanticSearch:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.retrieval = RetrievalEngine(store or enterprise_hub_store)

    def search(self, *, query: str, mode: str = "semantic", top_k: int = 5) -> dict[str, Any]:
        return self.retrieval.retrieve(query=query, mode=mode, top_k=top_k)
