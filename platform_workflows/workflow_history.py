"""Epic 45.3 — workflow run history."""
from __future__ import annotations
from typing import Any
from platform_workflows.ua_store import ua_store

class WorkflowHistory:
    def record(self, entry: dict[str, Any]) -> None:
        ua_store.history.append(entry)
    def list_for(self, owner_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        items = [h for h in ua_store.history if h.get("owner_id") == owner_id]
        return list(reversed(items[-limit:]))
    def for_workflow(self, workflow_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        items = [h for h in ua_store.history if h.get("workflow_id") == workflow_id]
        return list(reversed(items[-limit:]))

workflow_history = WorkflowHistory()
