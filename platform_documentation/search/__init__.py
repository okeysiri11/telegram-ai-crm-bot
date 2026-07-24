"""Documentation search — Sprint 21.6."""

from __future__ import annotations

from typing import Any


class DocumentationSearch:
    def __init__(self) -> None:
        self._index: list[dict[str, Any]] = []

    def index(self, docs: list[dict[str, Any]]) -> int:
        self._index.extend(docs)
        return len(docs)

    def search(
        self,
        *,
        query: str = "",
        category: str | None = None,
        module: str | None = None,
        version: str | None = None,
        doc_type: str | None = None,
    ) -> dict[str, Any]:
        q = query.lower().strip()
        hits = []
        for doc in self._index:
            if category and doc.get("category") != category:
                continue
            if module and doc.get("module") != module:
                continue
            if version and doc.get("version") != version:
                continue
            if doc_type and doc.get("kind") != doc_type and doc.get("type") != doc_type:
                continue
            blob = " ".join(str(v) for v in doc.values()).lower()
            if q and q not in blob:
                continue
            hits.append(doc)
        return {"query": query, "count": len(hits), "hits": hits}
