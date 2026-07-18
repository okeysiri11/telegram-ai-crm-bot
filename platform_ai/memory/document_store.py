# Document store — raw knowledge document persistence.

from __future__ import annotations

from typing import Any

from platform_ai.memory.exceptions import KnowledgeNotFoundError
from platform_ai.memory.models import KnowledgeDocument


class DocumentStore:
    def __init__(self) -> None:
        self._documents: dict[str, KnowledgeDocument] = {}

    def reset(self) -> None:
        self._documents.clear()

    def save(self, doc: KnowledgeDocument) -> KnowledgeDocument:
        self._documents[doc.document_id] = doc
        return doc

    def get(self, document_id: str) -> KnowledgeDocument:
        if document_id not in self._documents:
            raise KnowledgeNotFoundError(document_id)
        return self._documents[document_id]

    def delete(self, document_id: str) -> bool:
        return self._documents.pop(document_id, None) is not None

    def list_all(self, **filters: Any) -> list[KnowledgeDocument]:
        results = list(self._documents.values())
        if plugin_id := filters.get("plugin_id"):
            results = [d for d in results if d.plugin_id == plugin_id]
        if doc_type := filters.get("doc_type"):
            results = [d for d in results if d.doc_type == doc_type]
        if tag := filters.get("tag"):
            results = [d for d in results if tag in d.tags]
        return results

    def count(self) -> int:
        return len(self._documents)

    def total_content_bytes(self) -> int:
        return sum(len(d.content) for d in self._documents.values())


document_store = DocumentStore()
