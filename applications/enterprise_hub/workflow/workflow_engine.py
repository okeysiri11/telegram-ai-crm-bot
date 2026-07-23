"""Workflow engine — trigger → conditions → actions → result."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.workflow.models import TRIGGERS
from applications.enterprise_hub.workflow.workflow_executor import WorkflowExecutor
from applications.enterprise_hub.workflow.workflow_manager import WorkflowManager
from applications.enterprise_hub.workflow.workflow_validator import WorkflowValidator


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WorkflowEngine:
    def __init__(
        self,
        store: EnterpriseHubStore | None = None,
        *,
        manager: WorkflowManager | None = None,
        validator: WorkflowValidator | None = None,
        executor: WorkflowExecutor | None = None,
    ) -> None:
        self.store = store or enterprise_hub_store
        self.manager = manager or WorkflowManager(self.store)
        self.validator = validator or WorkflowValidator(self.store)
        self.executor = executor or WorkflowExecutor(self.store)

    def run(
        self,
        *,
        workflow_id: str = "",
        trigger: str = "",
        name: str = "",
        executor: str = "system",
        context: dict[str, Any] | None = None,
        blocks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        wid = workflow_id
        if not wid:
            tr = (trigger or "api").lower().strip()
            if tr not in TRIGGERS:
                raise ValidationError(f"trigger must be one of {list(TRIGGERS)}")
            created = self.manager.create(
                name=name or f"ad-hoc-{tr}",
                trigger=tr,
                blocks=blocks,
            )
            self.manager.publish(workflow_id=created["workflow_id"])
            wid = created["workflow_id"]
        self.validator.require_valid(workflow_id=wid)
        run = self.executor.execute(workflow_id=wid, executor=executor, context=context)
        eid = _id("wf_eng")
        return self.store.wf_engine_runs.save(
            eid,
            {
                "engine_run_id": eid,
                "workflow_id": wid,
                "execution_id": run["execution_id"],
                "result": run["result"],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "engine_runs": self.store.wf_engine_runs.count(),
            "manager": self.manager.status(),
            "validator": self.validator.status(),
            "executor": self.executor.status(),
        }
