# Knowledge base — document lifecycle management.

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from platform_ai.memory.chunking import chunker
from platform_ai.memory.document_store import document_store
from platform_ai.memory.knowledge_index import knowledge_index
from platform_ai.memory.knowledge_loader import knowledge_loader
from platform_ai.memory.memory_embeddings import embedding_registry
from platform_ai.memory.models import IndexRequest, KnowledgeDocument

logger = logging.getLogger(__name__)


class KnowledgeBase:
    async def index(self, request: IndexRequest, *, provider_id: str | None = None) -> KnowledgeDocument:
        loaded = knowledge_loader.load(request.content, request.doc_type, title=request.title)
        text = loaded["text"]
        metadata = {**request.metadata, **loaded.get("metadata", {})}

        doc = KnowledgeDocument(
            document_id=request.document_id,
            title=request.title,
            content=text,
            doc_type=request.doc_type,
            plugin_id=request.plugin_id,
            tags=list(request.tags),
            metadata=metadata,
        )

        chunks = chunker.chunk(
            text,
            doc.document_id,
            strategy=request.chunk_strategy,
            metadata={"title": doc.title, "doc_type": doc.doc_type, "tags": doc.tags},
        )

        provider = embedding_registry.get(provider_id)
        texts = [c.content for c in chunks]
        embeddings = await provider.embed_batch(texts)
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb

        knowledge_index.remove_document(doc.document_id)
        knowledge_index.add_chunks(chunks)
        doc.chunk_count = len(chunks)
        document_store.save(doc)
        logger.info("knowledge_indexed doc=%s chunks=%d", doc.document_id, len(chunks))
        return doc

    async def update(self, document_id: str, content: str, *, title: str | None = None) -> KnowledgeDocument:
        doc = document_store.get(document_id)
        doc.content = content
        if title:
            doc.title = title
        doc.updated_at = datetime.now(timezone.utc).isoformat()
        request = IndexRequest(
            document_id=doc.document_id,
            title=doc.title,
            content=doc.content,
            doc_type=doc.doc_type,
            plugin_id=doc.plugin_id,
            tags=doc.tags,
            metadata=doc.metadata,
        )
        return await self.index(request)

    def delete(self, document_id: str) -> bool:
        knowledge_index.remove_document(document_id)
        return document_store.delete(document_id)

    async def rebuild(self, document_id: str | None = None, *, provider_id: str | None = None) -> dict[str, Any]:
        if document_id:
            doc = document_store.get(document_id)
            request = IndexRequest(
                document_id=doc.document_id,
                title=doc.title,
                content=doc.content,
                doc_type=doc.doc_type,
                plugin_id=doc.plugin_id,
                tags=doc.tags,
                metadata=doc.metadata,
            )
            await self.index(request, provider_id=provider_id)
            return {"rebuilt": 1, "document_id": document_id}
        docs = document_store.list_all()
        for doc in docs:
            request = IndexRequest(
                document_id=doc.document_id,
                title=doc.title,
                content=doc.content,
                doc_type=doc.doc_type,
                plugin_id=doc.plugin_id,
                tags=doc.tags,
                metadata=doc.metadata,
            )
            await self.index(request, provider_id=provider_id)
        return {"rebuilt": len(docs)}

    def get(self, document_id: str) -> KnowledgeDocument:
        return document_store.get(document_id)

    def list_documents(self, **filters: Any) -> list[KnowledgeDocument]:
        return document_store.list_all(**filters)


knowledge_base = KnowledgeBase()
