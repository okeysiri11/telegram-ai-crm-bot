# Platform Memory — automatic prompt context assembly.

from __future__ import annotations

from platform_memory.config import DEFAULT_TOKEN_LIMITS, TokenLimits
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
from platform_memory.summarizer import MemorySummarizer, estimate_tokens, truncate_to_tokens


class ContextAssembler:
    """Builds prompt context from dialog, profile, history, agent, and project memory."""

    __slots__ = (
        "_conversation",
        "_user_profile",
        "_agent_memory",
        "_business_memory",
        "_session_memory",
        "_project_memory",
        "_summarizer",
        "_limits",
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
    ) -> None:
        self._conversation = conversation
        self._user_profile = user_profile
        self._agent_memory = agent_memory
        self._business_memory = business_memory
        self._session_memory = session_memory
        self._project_memory = project_memory
        self._summarizer = summarizer or MemorySummarizer()
        self._limits = limits or DEFAULT_TOKEN_LIMITS
        self._limits.validate()

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

        summarized = False
        history_text = "\n".join(f"{t.role}: {t.content}" for t in history)
        if estimate_tokens(history_text) > self._limits.history_summarize_at():
            history_text, history = self._summarizer.summarize_conversation(
                history,
                max_tokens=self._limits.max_history_tokens,
            )
            summarized = True

        history_text = truncate_to_tokens(history_text, self._limits.max_history_tokens)

        user_facts = []
        if request.user_id:
            user_facts = await self._user_profile.list_facts(request.user_id, limit=50)
        profile_text = "\n".join(f"{f.key}: {f.value}" for f in user_facts)
        profile_text = truncate_to_tokens(profile_text, self._limits.max_profile_tokens)

        agent_records = await self._agent_memory.list_memory(
            agent_id=request.agent_id,
            user_id=request.user_id,
            limit=50,
        )
        agent_text = "\n".join(r.content for r in agent_records)
        agent_text = truncate_to_tokens(agent_text, self._limits.max_memory_tokens)

        business_facts = []
        if request.organization_id:
            business_facts = await self._business_memory.list_facts(request.organization_id, limit=50)
        business_text = "\n".join(f"{f.key}: {f.value}" for f in business_facts)
        business_text = truncate_to_tokens(business_text, self._limits.max_business_tokens)

        project_records = []
        if request.project_id:
            project_records = await self._project_memory.list_memory(request.project_id, limit=50)
        project_text = "\n".join(r.content for r in project_records)
        project_text = truncate_to_tokens(project_text, self._limits.max_project_tokens)

        session_records = await self._session_memory.list_memory(
            session_id=request.session_id,
            user_id=request.user_id,
            limit=50,
        )
        session_text = "\n".join(r.content for r in session_records)
        session_text = truncate_to_tokens(session_text, self._limits.max_session_tokens)

        sections = {
            "conversation_history": history_text,
            "user_profile": profile_text,
            "agent_memory": agent_text,
            "business_facts": business_text,
            "project_memory": project_text,
            "session_memory": session_text,
            "configuration": dict(request.configuration),
        }

        prompt_parts = [
            ("Conversation", history_text),
            ("User profile", profile_text),
            ("Agent memory", agent_text),
            ("Business facts", business_text),
            ("Project memory", project_text),
            ("Session memory", session_text),
        ]
        prompt_context = self._build_prompt(prompt_parts)
        if estimate_tokens(prompt_context) > self._limits.max_context_tokens:
            prompt_context = truncate_to_tokens(prompt_context, self._limits.max_context_tokens)
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
        agent_records = await self._agent_memory.list_memory(
            agent_id=request.agent_id,
            user_id=request.user_id,
            limit=20,
        )

        return AIContextBundle(
            relevant_memory=[r.to_dict() for r in agent_records],
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
