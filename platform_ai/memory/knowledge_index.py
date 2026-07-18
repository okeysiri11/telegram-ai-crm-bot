# Knowledge index — chunk storage with embeddings for retrieval.

from __future__ import annotations

from typing import Any

from platform_ai.memory.models import DocumentChunk


class KnowledgeIndex:
    def __init__(self) -> None:
        self._chunks: dict[str, DocumentChunk] = {}
        self._by_document: dict[str, list[str]] = {}

    def reset(self) -> None:
        self._chunks.clear()
        self._by_document.clear()

    def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        for chunk in chunks:
            self._chunks[chunk.chunk_id] = chunk
            doc_chunks = self._by_document.setdefault(chunk.document_id, [])
            if chunk.chunk_id not in doc_chunks:
                doc_chunks.append(chunk.chunk_id)
        return len(chunks)

    def remove_document(self, document_id: str) -> int:
        chunk_ids = self._by_document.pop(document_id, [])
        for cid in chunk_ids:
            self._chunks.pop(cid, None)
        return len(chunk_ids)

    def get_chunks(self, document_id: str | None = None) -> list[DocumentChunk]:
        if document_id:
            return [self._chunks[cid] for cid in self._by_document.get(document_id, []) if cid in self._chunks]
        return list(self._chunks.values())

    def count(self) -> int:
        return len(self._chunks)

    def stats(self) -> dict[str, Any]:
        return {
            "total_chunks": len(self._chunks),
            "documents_indexed": len(self._by_document),
        }


knowledge_index = KnowledgeIndex()
