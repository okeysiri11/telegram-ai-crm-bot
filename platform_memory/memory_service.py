# Platform Memory — centralized memory service.

from __future__ import annotations

import logging
from typing import Any

from events.base_event import BaseEvent
from platform_memory.config import DEFAULT_SEMANTIC_CONFIG, DEFAULT_TOKEN_LIMITS, SemanticMemoryConfig, TokenLimits
from platform_memory.context_assembler import ContextAssembler
from platform_memory.entities import MemoryEntity, MemoryFilters
from platform_memory.memory_events import (
    ContextAssembledEvent,
    ConversationAppendedEvent,
    MemoryStoredEvent,
    UserFactStoredEvent,
)
from platform_memory.models import (
    AIContextBundle,
    ContextAssemblyRequest,
    ContextAssemblyResult,
    ConversationRole,
    MemoryCategory,
)
from platform_memory.providers.embedding_provider import DummyEmbeddingProvider, EmbeddingProvider
from platform_memory.repositories.in_memory_semantic_repository import InMemoryMemoryRepository
from platform_memory.repositories.memory_repository import MemoryRepository
from platform_memory.providers.base import MemoryProviderBundle
from platform_memory.providers.in_memory import build_in_memory_providers
from platform_memory.search.memory_search_service import MemorySearchService
from platform_memory.repositories.agent_memory_repository import AgentMemoryRepository
from platform_memory.repositories.business_memory_repository import BusinessMemoryRepository
from platform_memory.repositories.conversation_history_repository import ConversationHistoryRepository
from platform_memory.repositories.project_memory_repository import ProjectMemoryRepository
from platform_memory.repositories.session_memory_repository import SessionMemoryRepository
from platform_memory.repositories.user_profile_repository import UserProfileRepository
from platform_memory.summarizer import MemorySummarizer

logger = logging.getLogger(__name__)


async def _publish(event: BaseEvent) -> None:
    from events.publisher import publish

    await publish(event, wait=True)


class MemoryService:
    """Platform-wide AI memory — persistent context for every agent."""

    def __init__(
        self,
        *,
        providers: MemoryProviderBundle | None = None,
        limits: TokenLimits | None = None,
        semantic_config: SemanticMemoryConfig | None = None,
        summarizer: MemorySummarizer | None = None,
        memory_repository: MemoryRepository | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        bundle = providers or build_in_memory_providers()
        self._providers = bundle
        self._limits = limits or DEFAULT_TOKEN_LIMITS
        self._semantic_config = semantic_config or DEFAULT_SEMANTIC_CONFIG
        self._memory_repository = memory_repository or InMemoryMemoryRepository()
        self._embedding = embedding_provider or DummyEmbeddingProvider()
        self._memory_search = MemorySearchService(
            repository=self._memory_repository,
            embedding=self._embedding,
            config=self._semantic_config,
        )
        self._conversation = ConversationHistoryRepository(bundle.conversation)
        self._user_profile = UserProfileRepository(bundle.user_profile)
        self._agent_memory = AgentMemoryRepository(bundle.agent_memory)
        self._business_memory = BusinessMemoryRepository(bundle.business_memory)
        self._session_memory = SessionMemoryRepository(bundle.session_memory)
        self._project_memory = ProjectMemoryRepository(bundle.project_memory)
        self._assembler = ContextAssembler(
            conversation=self._conversation,
            user_profile=self._user_profile,
            agent_memory=self._agent_memory,
            business_memory=self._business_memory,
            session_memory=self._session_memory,
            project_memory=self._project_memory,
            summarizer=summarizer,
            limits=self._limits,
            memory_search=self._memory_search,
            semantic_config=self._semantic_config,
        )
        self._initialized = False

    @property
    def token_limits(self) -> TokenLimits:
        return self._limits

    @property
    def semantic_config(self) -> SemanticMemoryConfig:
        return self._semantic_config

    @property
    def memory_search(self) -> MemorySearchService:
        return self._memory_search

    @property
    def context_assembler(self) -> ContextAssembler:
        return self._assembler

    def reset(self) -> None:
        limits = self._limits
        semantic = self._semantic_config
        self.__init__(limits=limits, semantic_config=semantic)
        self._initialized = False

    async def async_reset(self) -> None:
        await self._providers.clear_all()
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        logger.info("platform_memory_service_initialized")

    async def append_conversation(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        plugin_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        turn = await self._conversation.append_message(
            session_id=session_id,
            role=role,
            content=content,
            user_id=user_id,
            agent_id=agent_id,
            plugin_id=plugin_id,
            metadata=metadata,
        )
        await _publish(
            ConversationAppendedEvent(session_id=session_id, turn_id=turn.turn_id, role=role)
        )
        return turn.to_dict()

    async def remember_user_fact(
        self,
        *,
        user_id: str,
        key: str,
        value: str,
        source: str = "explicit",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        fact = await self._user_profile.remember_fact(
            user_id=user_id,
            key=key,
            value=value,
            source=source,
            metadata=metadata,
        )
        await _publish(UserFactStoredEvent(user_id=user_id, key=key))
        return fact.to_dict()

    async def remember_business_fact(
        self,
        *,
        organization_id: str,
        key: str,
        value: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        fact = await self._business_memory.remember_fact(
            organization_id=organization_id,
            key=key,
            value=value,
            metadata=metadata,
        )
        return fact.to_dict()

    async def remember_agent_memory(
        self,
        *,
        agent_id: str,
        content: str,
        memory_key: str = "",
        user_id: str | None = None,
        session_id: str | None = None,
        category: str = MemoryCategory.LONG_TERM.value,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        record = await self._agent_memory.remember(
            agent_id=agent_id,
            content=content,
            memory_key=memory_key,
            user_id=user_id,
            session_id=session_id,
            category=category,
            metadata=metadata,
        )
        await _publish(
            MemoryStoredEvent(memory_id=record.memory_id, category=category, agent_id=agent_id)
        )
        return record.to_dict()

    async def remember_session_memory(
        self,
        *,
        session_id: str,
        content: str,
        memory_key: str = "",
        user_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        record = await self._session_memory.remember(
            session_id=session_id,
            content=content,
            memory_key=memory_key,
            user_id=user_id,
            agent_id=agent_id,
            metadata=metadata,
        )
        return record.to_dict()

    async def remember_project_memory(
        self,
        *,
        project_id: str,
        content: str,
        memory_key: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        record = await self._project_memory.remember(
            project_id=project_id,
            content=content,
            memory_key=memory_key,
            metadata=metadata,
        )
        return record.to_dict()

    async def remember_semantic(
        self,
        *,
        text: str,
        owner_id: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        summary: str | None = None,
        importance_score: float = 0.5,
        expires_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        embedding = await self._embedding.embed(text)
        entity = MemoryEntity.create(
            text=text,
            embedding=embedding,
            owner_id=owner_id,
            agent_id=agent_id,
            session_id=session_id,
            summary=summary,
            importance_score=importance_score,
            expires_at=expires_at,
            metadata=metadata,
        )
        saved = await self._memory_repository.save(entity)
        await _publish(
            MemoryStoredEvent(
                memory_id=saved.id,
                category=MemoryCategory.LONG_TERM.value,
                agent_id=agent_id or "",
            )
        )
        return saved.to_dict()

    async def search_semantic(
        self,
        query: str,
        *,
        owner_id: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        self.initialize()
        filters = MemoryFilters(owner_id=owner_id, agent_id=agent_id, session_id=session_id)
        hits = await self._memory_search.search(query, filters=filters, limit=limit)
        return [hit.to_dict() for hit in hits]

    async def assemble_context(self, request: ContextAssemblyRequest) -> ContextAssemblyResult:
        self.initialize()
        result = await self._assembler.assemble(request)
        await _publish(
            ContextAssembledEvent(
                session_id=request.session_id or "",
                total_tokens=result.total_tokens,
                summarized=result.summarized,
            )
        )
        return result

    async def build_ai_context(self, **kwargs: Any) -> AIContextBundle:
        self.initialize()
        request = ContextAssemblyRequest(
            session_id=kwargs.get("session_id"),
            user_id=kwargs.get("user_id"),
            agent_id=kwargs.get("agent_id"),
            plugin_id=kwargs.get("plugin_id"),
            organization_id=kwargs.get("organization_id"),
            project_id=kwargs.get("project_id"),
            current_message=kwargs.get("current_message") or kwargs.get("query"),
            query=kwargs.get("query"),
            configuration=dict(kwargs.get("configuration") or {}),
        )
        bundle = await self._assembler.assemble_bundle(request)

        # Enrich with legacy knowledge retrieval when available.
        try:
            from platform_ai.memory.memory_retriever import memory_retriever
            from platform_ai.memory.models import SearchMode

            query = kwargs.get("query") or kwargs.get("current_message") or ""
            if query:
                results = await memory_retriever.search(
                    query,
                    plugin_id=kwargs.get("plugin_id"),
                    user_id=kwargs.get("user_id"),
                    limit=int(kwargs.get("limit", 5)),
                    mode=SearchMode.HYBRID.value,
                )
                bundle.relevant_knowledge = [r.to_dict() for r in results if r.source_type == "knowledge"]
                memory_hits = [r.to_dict() for r in results if r.source_type == "memory"]
                bundle.relevant_memory = memory_hits + bundle.relevant_memory
        except Exception:
            logger.debug("knowledge_retrieval_skipped", exc_info=True)

        return bundle

    async def inject_context(self, context: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        bundle = await self.build_ai_context(**kwargs)
        merged = dict(context)
        merged["memory"] = bundle.to_dict()
        merged["prompt_context"] = bundle.prompt_context
        merged["relevant_memory"] = bundle.relevant_memory
        merged["relevant_knowledge"] = bundle.relevant_knowledge
        merged["conversation_history"] = bundle.conversation_history
        return merged

    def statistics(self) -> dict[str, Any]:
        return {
            "token_limits": {
                "max_context_tokens": self._limits.max_context_tokens,
                "max_history_tokens": self._limits.max_history_tokens,
                "summarize_threshold_ratio": self._limits.summarize_threshold_ratio,
            },
            "semantic_config": {
                "max_context_tokens": self._semantic_config.max_context_tokens,
                "max_memories": self._semantic_config.max_memories,
                "similarity_threshold": self._semantic_config.similarity_threshold,
                "importance_weight": self._semantic_config.importance_weight,
                "recency_weight": self._semantic_config.recency_weight,
            },
            "providers": "in_memory",
            "embedding_provider": "dummy",
        }


memory_service = MemoryService()
