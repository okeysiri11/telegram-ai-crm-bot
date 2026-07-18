# Memory manager — lifecycle, permissions, compression.

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from platform_ai.memory.exceptions import MemoryNotFoundError, MemoryPermissionError
from platform_ai.memory.memory_registry import memory_registry
from platform_ai.memory.memory_store import memory_store
from platform_ai.memory.models import MemoryRecord, MemoryType, RememberRequest

logger = logging.getLogger(__name__)


class MemoryManager:
    def remember(self, request: RememberRequest) -> MemoryRecord:
        if request.memory_type not in memory_registry.list_types():
            request.memory_type = MemoryType.CONVERSATION.value

        existing = None
        if request.key:
            existing = memory_store.get_by_key(
                request.key,
                plugin_id=request.plugin_id,
                user_id=request.user_id,
                workflow_id=request.workflow_id,
                session_id=request.session_id,
            )

        if existing:
            existing.content = request.content
            existing.metadata = {**existing.metadata, **request.metadata}
            return memory_store.save(existing)

        record = MemoryRecord(
            memory_id=request.memory_id,
            memory_type=request.memory_type,
            content=request.content,
            key=request.key,
            plugin_id=request.plugin_id,
            user_id=request.user_id,
            workflow_id=request.workflow_id,
            session_id=request.session_id,
            organization_id=request.organization_id,
            metadata=dict(request.metadata),
        )
        return memory_store.save(record)

    def recall(self, memory_id: str | None = None, *, key: str | None = None, **scope: Any) -> MemoryRecord | list[MemoryRecord]:
        if memory_id:
            return memory_store.get(memory_id)
        if key:
            found = memory_store.get_by_key(key, **scope)
            if not found:
                raise MemoryNotFoundError(key)
            return found
        return memory_store.list_all(**scope)

    def forget(self, memory_id: str) -> bool:
        from platform_ai.memory.memory_retriever import memory_retriever

        memory_retriever.invalidate_cache()
        return memory_store.delete(memory_id)

    async def summarize(self, **filters: Any) -> dict[str, Any]:
        records = memory_store.list_all(**filters)
        if not records:
            return {"summary": "", "count": 0}
        combined = "\n".join(r.content[:500] for r in records[:20])
        try:
            from platform_ai.ai_service import ai_service
            from platform_ai.models import AIRequest, TaskType

            ai_service.initialize()
            response = await ai_service.complete(
                AIRequest(prompt=f"Summarize these memories concisely:\n\n{combined}", task_type=TaskType.SUMMARIZATION)
            )
            return {"summary": response.content, "count": len(records)}
        except Exception:
            return {"summary": combined[:1000], "count": len(records), "fallback": True}

    def compress(self, **filters: Any) -> dict[str, Any]:
        records = memory_store.list_all(**filters)
        temp_records = [r for r in records if r.memory_type == MemoryType.TEMPORARY.value]
        removed = 0
        for r in temp_records:
            if len(r.content) > 2000:
                r.content = r.content[:2000] + "...[compressed]"
                memory_store.save(r)
                removed += 1
        return {"compressed": removed, "total_scanned": len(records)}

    def check_permission(self, *, plugin_id: str | None, action: str = "read") -> None:
        if action == "admin":
            raise MemoryPermissionError("Admin permission required")

    def statistics(self) -> dict[str, Any]:
        return {
            "memory": memory_store.stats(),
            "registry": memory_registry.summary(),
        }


memory_manager = MemoryManager()
