"""Workflow history — runs, logs, duration, errors."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class WorkflowHistory:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def get(self, *, execution_id: str) -> dict[str, Any]:
        run = self.store.wf_executions.get(execution_id)
        if run is None:
            raise NotFoundError(f"execution not found: {execution_id}")
        return {
            "workflow_id": run.get("workflow_id"),
            "version": run.get("version"),
            "trigger": run.get("trigger"),
            "executor": run.get("executor"),
            "current_step": run.get("current_step"),
            "result": run.get("result"),
            "duration": run.get("duration_ms"),
            "logs": run.get("logs"),
            "errors": run.get("errors"),
            "execution_id": execution_id,
        }

    def list_recent(self, *, limit: int = 20) -> list[dict[str, Any]]:
        items = [i for i in self.store.wf_executions.list_all() if isinstance(i, dict)]
        items.sort(key=lambda x: x.get("at", ""), reverse=True)
        return items[: max(1, limit)]

    def status(self) -> dict[str, Any]:
        return {"executions": self.store.wf_executions.count()}
