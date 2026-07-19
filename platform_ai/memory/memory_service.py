# Memory service — single entry point for all AI memory & knowledge operations.

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from events.base_event import BaseEvent

from platform_ai.memory.document_store import document_store
from platform_ai.memory.knowledge_base import knowledge_base
from platform_ai.memory.knowledge_index import knowledge_index
from platform_ai.memory.knowledge_search import knowledge_search
from platform_ai.memory.memory_context import memory_context_builder
from platform_ai.memory.memory_embeddings import embedding_registry
from platform_ai.memory.memory_manager import memory_manager
from platform_ai.memory.memory_registry import memory_registry
from platform_ai.memory.memory_retriever import memory_retriever
from platform_ai.memory.memory_store import memory_store
from platform_ai.memory.models import AIContextBundle, IndexRequest, RememberRequest, SearchMode

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class MemoryCreatedEvent(BaseEvent):
    memory_id: str = ""
    memory_type: str = ""
    plugin_id: str = ""


@dataclass(kw_only=True)
class MemoryUpdatedEvent(BaseEvent):
    memory_id: str = ""
    memory_type: str = ""


@dataclass(kw_only=True)
class MemoryDeletedEvent(BaseEvent):
    memory_id: str = ""


@dataclass(kw_only=True)
class KnowledgeIndexedEvent(BaseEvent):
    document_id: str = ""
    chunk_count: int = 0


@dataclass(kw_only=True)
class KnowledgeUpdatedEvent(BaseEvent):
    document_id: str = ""


@dataclass(kw_only=True)
class KnowledgeSearchEvent(BaseEvent):
    query: str = ""
    result_count: int = 0


async def _publish(event: BaseEvent) -> None:
    from events.publisher import publish

    await publish(event, wait=True)


class MemoryService:
    """Centralized Memory & Knowledge Platform — no AI module implements its own memory."""

    def __init__(self) -> None:
        self._initialized = False

    def reset(self) -> None:
        memory_store.reset()
        document_store.reset()
        knowledge_index.reset()
        memory_retriever.reset()
        embedding_registry.reset()
        memory_registry.reset()
        from platform_memory.memory_service import memory_service as platform_memory_service

        platform_memory_service.reset()
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        logger.info("memory_service_initialized")

    # ---- Memory API ----

    async def remember(self, request: RememberRequest) -> dict[str, Any]:
        self.initialize()
        record = memory_manager.remember(request)
        memory_retriever.invalidate_cache()
        await _publish(
            MemoryCreatedEvent(
                memory_id=record.memory_id,
                memory_type=record.memory_type,
                plugin_id=record.plugin_id or "",
            )
        )
        return record.to_dict()

    def recall(self, memory_id: str | None = None, *, key: str | None = None, **scope: Any) -> Any:
        self.initialize()
        result = memory_manager.recall(memory_id, key=key, **scope)
        if isinstance(result, list):
            return [r.to_dict() for r in result]
        return result.to_dict()

    async def forget(self, memory_id: str) -> dict[str, Any]:
        self.initialize()
        deleted = memory_manager.forget(memory_id)
        if deleted:
            await _publish(MemoryDeletedEvent(memory_id=memory_id))
        return {"deleted": deleted, "memory_id": memory_id}

    async def search(
        self,
        query: str,
        *,
        mode: str = SearchMode.HYBRID.value,
        limit: int = 10,
        **filters: Any,
    ) -> dict[str, Any]:
        self.initialize()
        results = await memory_retriever.search(query, mode=mode, limit=limit, **filters)
        await _publish(KnowledgeSearchEvent(query=query, result_count=len(results)))
        return {
            "query": query,
            "mode": mode,
            "results": [r.to_dict() for r in results],
            "count": len(results),
            "latency_ms": memory_retriever.last_latency_ms,
        }

    async def summarize(self, **filters: Any) -> dict[str, Any]:
        self.initialize()
        return await memory_manager.summarize(**filters)

    def compress(self, **filters: Any) -> dict[str, Any]:
        self.initialize()
        return memory_manager.compress(**filters)

    # ---- Knowledge API ----

    async def index(self, request: IndexRequest, *, provider_id: str | None = None) -> dict[str, Any]:
        self.initialize()
        doc = await knowledge_base.index(request, provider_id=provider_id)
        memory_retriever.invalidate_cache()
        await _publish(KnowledgeIndexedEvent(document_id=doc.document_id, chunk_count=doc.chunk_count))
        return doc.to_dict()

    async def update_knowledge(self, document_id: str, content: str, *, title: str | None = None) -> dict[str, Any]:
        self.initialize()
        doc = await knowledge_base.update(document_id, content, title=title)
        memory_retriever.invalidate_cache()
        await _publish(KnowledgeUpdatedEvent(document_id=document_id))
        return doc.to_dict()

    async def delete_knowledge(self, document_id: str) -> dict[str, Any]:
        self.initialize()
        deleted = knowledge_base.delete(document_id)
        memory_retriever.invalidate_cache()
        return {"deleted": deleted, "document_id": document_id}

    async def search_knowledge(self, query: str, **options: Any) -> dict[str, Any]:
        self.initialize()
        result = await knowledge_search.search(query, **options)
        await _publish(KnowledgeSearchEvent(query=query, result_count=result.get("count", 0)))
        return result

    async def rebuild_index(self, document_id: str | None = None, *, provider_id: str | None = None) -> dict[str, Any]:
        self.initialize()
        result = await knowledge_base.rebuild(document_id, provider_id=provider_id)
        memory_retriever.invalidate_cache()
        return result

    # ---- AI Context ----

    async def build_ai_context(self, **kwargs: Any) -> AIContextBundle:
        self.initialize()
        from platform_memory.memory_service import memory_service as platform_memory_service

        bundle = await platform_memory_service.build_ai_context(**kwargs)
        return AIContextBundle(
            relevant_memory=bundle.relevant_memory,
            relevant_knowledge=bundle.relevant_knowledge,
            conversation_history=bundle.conversation_history,
            plugin_context=bundle.plugin_context,
            configuration=bundle.configuration,
        )

    async def inject_context(self, context: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Merge memory/knowledge bundle into an existing AI execution context."""
        bundle = await self.build_ai_context(**kwargs)
        merged = dict(context)
        merged["memory"] = bundle.to_dict()
        merged["relevant_memory"] = bundle.relevant_memory
        merged["relevant_knowledge"] = bundle.relevant_knowledge
        merged["conversation_history"] = bundle.conversation_history
        return merged

    # ---- Management ----

    def list_documents(self, **filters: Any) -> list[dict[str, Any]]:
        self.initialize()
        return [d.to_dict() for d in knowledge_base.list_documents(**filters)]

    def statistics(self) -> dict[str, Any]:
        self.initialize()
        return {
            "memory": memory_store.stats(),
            "knowledge": {
                "documents": document_store.count(),
                "content_bytes": document_store.total_content_bytes(),
                "index": knowledge_index.stats(),
            },
            "embeddings": embedding_registry.list_providers(),
            "search_cache_entries": len(memory_retriever._cache),
            "last_search_latency_ms": memory_retriever.last_latency_ms,
        }


memory_service = MemoryService()
