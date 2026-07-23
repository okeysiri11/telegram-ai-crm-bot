"""Context manager — shared task context and agent handoff."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_orchestrator.task_manager import TaskManager
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ContextManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tasks = TaskManager(self.store)

    def open(self, *, task_id: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
        self.tasks.get(task_id)
        cid = _id("aop_ctx")
        return self.store.aop_contexts.save(
            cid,
            {
                "context_id": cid,
                "task_id": task_id,
                "shared": seed or {},
                "history": [],
                "created_at": _now(),
            },
        )

    def append(
        self,
        *,
        context_id: str,
        agent_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        ctx = self.store.aop_contexts.get(context_id)
        if not ctx:
            from applications.enterprise_hub.shared.exceptions import NotFoundError

            raise NotFoundError(f"context not found: {context_id}")
        entry = {"agent_id": agent_id, "payload": payload, "at": _now()}
        ctx.setdefault("history", []).append(entry)
        ctx.setdefault("shared", {}).update(payload)
        return self.store.aop_contexts.save(context_id, ctx)

    def get(self, context_id: str) -> dict[str, Any]:
        from applications.enterprise_hub.shared.exceptions import NotFoundError

        item = self.store.aop_contexts.get(context_id)
        if not item:
            raise NotFoundError(f"context not found: {context_id}")
        return item
