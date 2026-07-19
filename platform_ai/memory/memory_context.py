# AI context builder — delegates to platform_memory ContextAssembler.

from __future__ import annotations

from typing import Any

from platform_memory.memory_service import memory_service as platform_memory_service
from platform_ai.memory.models import AIContextBundle


class MemoryContextBuilder:
    async def build(
        self,
        *,
        query: str | None = None,
        plugin_id: str | None = None,
        user_id: str | None = None,
        workflow_id: str | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
        organization_id: str | None = None,
        project_id: str | None = None,
        configuration: dict[str, Any] | None = None,
        limit: int = 5,
    ) -> AIContextBundle:
        bundle = await platform_memory_service.build_ai_context(
            query=query,
            plugin_id=plugin_id,
            user_id=user_id,
            session_id=session_id,
            agent_id=agent_id or workflow_id,
            organization_id=organization_id,
            project_id=project_id,
            configuration=configuration,
            limit=limit,
        )
        return AIContextBundle(
            relevant_memory=bundle.relevant_memory[:limit],
            relevant_knowledge=bundle.relevant_knowledge[:limit],
            conversation_history=bundle.conversation_history,
            plugin_context={
                **bundle.plugin_context,
                "workflow_id": workflow_id,
            },
            configuration=bundle.configuration,
        )


memory_context_builder = MemoryContextBuilder()
