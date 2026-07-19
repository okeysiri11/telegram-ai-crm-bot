# Platform Memory — automatic prompt context assembly.

from __future__ import annotations

from platform_memory.config import DEFAULT_SEMANTIC_CONFIG, DEFAULT_TOKEN_LIMITS, SemanticMemoryConfig, TokenLimits
from platform_memory.entities import MemoryFilters
from platform_memory.models import (
    AIContextBundle,
    ContextAssemblyRequest,
    ContextAssemblyResult,
    ConversationTurn,
)
from platform_memory.repositories.agent_memory_repository import AgentMemoryRepository
from platform_memory.repositories.business_memory_repository import BusinessMemoryRepository
from platform_memory.repositories.conversation_history_repository import ConversationHistoryRepository
from platform_memory.repositories.project_memory_repository import ProjectMemoryRepository
from platform_memory.repositories.session_memory_repository import SessionMemoryRepository
from platform_memory.repositories.user_profile_repository import UserProfileRepository
from platform_memory.search.memory_search_service import MemorySearchService
from platform_memory.summarizer import MemorySummarizer, estimate_tokens, truncate_to_tokens


class ContextAssembler:
    """Builds LLM prompt context with semantic memory priority."""

    __slots__ = (
        "_conversation",
        "_user_profile",
        "_agent_memory",
        "_business_memory",
        "_session_memory",
        "_project_memory",
        "_summarizer",
        "_limits",
        "_memory_search",
        "_semantic_config",
    )

    def __init__(
        self,
        *,
        conversation: ConversationHistoryRepository,
        user_profile: UserProfileRepository,
        agent_memory: AgentMemoryRepository,
        business_memory: BusinessMemoryRepository,
        session_memory: SessionMemoryRepository,
        project_memory: ProjectMemoryRepository,
        summarizer: MemorySummarizer | None = None,
        limits: TokenLimits | None = None,
        memory_search: MemorySearchService | None = None,
        semantic_config: SemanticMemoryConfig | None = None,
    ) -> None:
        self._conversation = conversation
        self._user_profile = user_profile
        self._agent_memory = agent_memory
        self._business_memory = business_memory
        self._session_memory = session_memory
        self._project_memory = project_memory
        self._summarizer = summarizer or MemorySummarizer()
        self._limits = limits or DEFAULT_TOKEN_LIMITS
        self._memory_search = memory_search
        self._semantic_config = semantic_config or DEFAULT_SEMANTIC_CONFIG
        self._limits.validate()
        self._semantic_config.validate()

    async def assemble(self, request: ContextAssemblyRequest) -> ContextAssemblyResult:
        history = await self._conversation.list_history(
            session_id=request.session_id,
            user_id=request.user_id,
            agent_id=request.agent_id,
            plugin_id=request.plugin_id,
            limit=200,
        )

        if request.current_message:
            history = list(history) + [
                ConversationTurn(
                    turn_id="current",
                    session_id=request.session_id or "ephemeral",
                    role="user",
                    content=request.current_message,
                    user_id=request.user_id,
                    agent_id=request.agent_id,
                    plugin_id=request.plugin_id,
                )
            ]

        current_turns = history[-4:] if len(history) > 4 else list(history)
        older_turns = history[:-4] if len(history) > 4 else []

        current_text = "\n".join(f"{t.role}: {t.content}" for t in current_turns)
        current_text = truncate_to_tokens(current_text, self._limits.max_history_tokens // 2)

        summarized = False
        summarized_history = ""
        if older_turns:
            older_text = "\n".join(f"{t.role}: {t.content}" for t in older_turns)
            if estimate_tokens(older_text) > self._limits.history_summarize_at() // 2:
                summarized_history, _ = self._summarizer.summarize_conversation(
                    older_turns,
                    max_tokens=self._limits.max_history_tokens // 2,
                )
                summarized = True
            else:
                summarized_history = older_text
            summarized_history = truncate_to_tokens(
                summarized_history,
                self._limits.max_history_tokens // 2,
            )

        semantic_text = ""
        important_text = ""
        recent_text = ""
        if self._memory_search is not None:
            filters = MemoryFilters(
                owner_id=request.user_id,
                agent_id=request.agent_id,
                session_id=request.session_id,
            )
            query = request.query or request.current_message or ""
            semantic_hits = await self._memory_search.search(query, filters=filters)
            important_hits = await self._memory_search.important(filters=filters, limit=5)
            recent_hits = await self._memory_search.recent(filters=filters, limit=5)

            seen: set[str] = set()

            def _lines(hits: list, label: str) -> str:
                nonlocal seen
                rows: list[str] = []
                for hit in hits:
                    if hit.entity.id in seen:
                        continue
                    seen.add(hit.entity.id)
                    body = hit.entity.summary or hit.entity.text
                    rows.append(f"- [{label} score={hit.score:.2f}] {body}")
                return "\n".join(rows)

            semantic_text = _lines(semantic_hits, "semantic")
            important_text = _lines(important_hits, "important")
            recent_text = _lines(recent_hits, "recent")

        else:
            agent_records = await self._agent_memory.list_memory(
                agent_id=request.agent_id,
                user_id=request.user_id,
                limit=50,
            )
            semantic_text = truncate_to_tokens(
                "\n".join(r.content for r in agent_records),
                self._limits.max_memory_tokens,
            )

        user_facts = []
        if request.user_id:
            user_facts = await self._user_profile.list_facts(request.user_id, limit=50)
        profile_text = truncate_to_tokens(
            "\n".join(f"{f.key}: {f.value}" for f in user_facts),
            self._limits.max_profile_tokens,
        )

        business_text = ""
        if request.organization_id:
            business_facts = await self._business_memory.list_facts(request.organization_id, limit=50)
            business_text = truncate_to_tokens(
                "\n".join(f"{f.key}: {f.value}" for f in business_facts),
                self._limits.max_business_tokens,
            )

        project_text = ""
        if request.project_id:
            project_records = await self._project_memory.list_memory(request.project_id, limit=50)
            project_text = truncate_to_tokens(
                "\n".join(r.content for r in project_records),
                self._limits.max_project_tokens,
            )

        session_records = await self._session_memory.list_memory(
            session_id=request.session_id,
            user_id=request.user_id,
            limit=50,
        )
        session_text = truncate_to_tokens(
            "\n".join(r.content for r in session_records),
            self._limits.max_session_tokens,
        )

        sections = {
            "current_conversation": current_text,
            "semantic_memories": semantic_text,
            "important_memories": important_text,
            "recent_memories": recent_text,
            "summarized_history": summarized_history,
            "user_profile": profile_text,
            "business_facts": business_text,
            "project_memory": project_text,
            "session_memory": session_text,
            "configuration": dict(request.configuration),
        }

        prompt_parts = [
            ("Current conversation", current_text),
            ("Semantic memories", semantic_text),
            ("Important memories", important_text),
            ("Recent memories", recent_text),
            ("Summarized history", summarized_history),
            ("User profile", profile_text),
            ("Business facts", business_text),
            ("Project memory", project_text),
            ("Session memory", session_text),
        ]
        max_tokens = min(self._limits.max_context_tokens, self._semantic_config.max_context_tokens)
        prompt_context = self._build_prompt(prompt_parts)
        if estimate_tokens(prompt_context) > max_tokens:
            prompt_context = truncate_to_tokens(prompt_context, max_tokens)
            summarized = True

        return ContextAssemblyResult(
            prompt_context=prompt_context,
            sections=sections,
            total_tokens=estimate_tokens(prompt_context),
            summarized=summarized,
            conversation_turn_count=len(history),
        )

    async def assemble_bundle(self, request: ContextAssemblyRequest) -> AIContextBundle:
        result = await self.assemble(request)
        history = await self._conversation.list_history(
            session_id=request.session_id,
            user_id=request.user_id,
            agent_id=request.agent_id,
            plugin_id=request.plugin_id,
            limit=50,
        )
        user_facts = (
            await self._user_profile.list_facts(request.user_id, limit=50) if request.user_id else []
        )
        business_facts = (
            await self._business_memory.list_facts(request.organization_id, limit=50)
            if request.organization_id
            else []
        )
        project_records = (
            await self._project_memory.list_memory(request.project_id, limit=50)
            if request.project_id
            else []
        )
        session_records = await self._session_memory.list_memory(
            session_id=request.session_id,
            user_id=request.user_id,
            limit=50,
        )

        semantic_memory: list[dict] = []
        if self._memory_search is not None:
            filters = MemoryFilters(
                owner_id=request.user_id,
                agent_id=request.agent_id,
                session_id=request.session_id,
            )
            query = request.query or request.current_message or ""
            semantic_memory = [hit.to_dict() for hit in await self._memory_search.search(query, filters=filters)]
        else:
            agent_records = await self._agent_memory.list_memory(
                agent_id=request.agent_id,
                user_id=request.user_id,
                limit=20,
            )
            semantic_memory = [r.to_dict() for r in agent_records]

        return AIContextBundle(
            relevant_memory=semantic_memory,
            conversation_history=[
                {"role": t.role, "content": t.content, "timestamp": t.created_at} for t in history
            ],
            user_profile=[f.to_dict() for f in user_facts],
            business_facts=[f.to_dict() for f in business_facts],
            project_memory=[r.to_dict() for r in project_records],
            session_memory=[r.to_dict() for r in session_records],
            plugin_context={
                "plugin_id": request.plugin_id,
                "user_id": request.user_id,
                "agent_id": request.agent_id,
                "session_id": request.session_id,
                "project_id": request.project_id,
                "organization_id": request.organization_id,
            },
            configuration=dict(request.configuration),
            prompt_context=result.prompt_context,
        )

    @staticmethod
    def _build_prompt(parts: list[tuple[str, str]]) -> str:
        blocks: list[str] = []
        for title, body in parts:
            if body.strip():
                blocks.append(f"## {title}\n{body.strip()}")
        return "\n\n".join(blocks)
