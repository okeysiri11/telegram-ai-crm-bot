# AI context builder — injects memory & knowledge into Skills and Workflows.

from __future__ import annotations

from typing import Any

from platform_ai.memory.memory_store import memory_store
from platform_ai.memory.models import AIContextBundle, MemoryType
from platform_ai.memory.memory_retriever import memory_retriever


class MemoryContextBuilder:
    async def build(
        self,
        *,
        query: str | None = None,
        plugin_id: str | None = None,
        user_id: str | None = None,
        workflow_id: str | None = None,
        session_id: str | None = None,
        configuration: dict[str, Any] | None = None,
        limit: int = 5,
    ) -> AIContextBundle:
        search_query = query or f"plugin:{plugin_id} user:{user_id}"

        results = await memory_retriever.search(
            search_query,
            plugin_id=plugin_id,
            user_id=user_id,
            limit=limit,
            use_cache=True,
        )

        relevant_memory = [r.to_dict() for r in results if r.source_type == "memory"]
        relevant_knowledge = [r.to_dict() for r in results if r.source_type == "knowledge"]

        conversation = memory_store.list_all(
            memory_type=MemoryType.CONVERSATION.value,
            plugin_id=plugin_id,
            user_id=user_id,
            session_id=session_id,
        )
        conversation_history = [
            {"role": m.metadata.get("role", "user"), "content": m.content, "timestamp": m.created_at}
            for m in conversation[:20]
        ]

        workflow_memory = []
        if workflow_id:
            wf_records = memory_store.list_all(memory_type=MemoryType.WORKFLOW.value, workflow_id=workflow_id)
            workflow_memory = [m.to_dict() for m in wf_records[:10]]
            relevant_memory = workflow_memory + relevant_memory

        return AIContextBundle(
            relevant_memory=relevant_memory[:limit],
            relevant_knowledge=relevant_knowledge[:limit],
            conversation_history=conversation_history,
            plugin_context={"plugin_id": plugin_id, "user_id": user_id, "workflow_id": workflow_id},
            configuration=dict(configuration or {}),
        )


memory_context_builder = MemoryContextBuilder()
