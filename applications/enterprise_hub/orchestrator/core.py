"""AI Orchestrator core — registry, execution, schedule, plan, queue, deps, retry, rollback."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class OrchestratorCore:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.workflow_kinds = list(DEFAULT_CONFIG.orch_workflow_kinds)

    def register_workflow(
        self, *, name: str, kind: str = "sequential", steps: list[str] | None = None
    ) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in self.workflow_kinds:
            raise ValidationError(f"kind must be one of {self.workflow_kinds}")
        if not name:
            raise ValidationError("name required")
        wid = _id("orch_wf")
        return self.store.orch_workflows.save(
            wid,
            {
                "workflow_id": wid,
                "name": name,
                "kind": k,
                "steps": steps or [],
                "status": "registered",
                "at": _now(),
            },
        )

    def plan(self, *, workflow_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        wf = self.store.orch_workflows.get(workflow_id)
        if wf is None:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        pid = _id("orch_plan")
        return self.store.orch_plans.save(
            pid,
            {
                "plan_id": pid,
                "workflow_id": workflow_id,
                "steps": wf["steps"],
                "context": context or {},
                "status": "planned",
                "at": _now(),
            },
        )

    def enqueue(self, *, plan_id: str, priority: int = 5) -> dict[str, Any]:
        if self.store.orch_plans.get(plan_id) is None:
            raise NotFoundError(f"plan not found: {plan_id}")
        qid = _id("orch_q")
        return self.store.orch_queue.save(
            qid,
            {
                "queue_id": qid,
                "plan_id": plan_id,
                "priority": int(priority),
                "status": "queued",
                "at": _now(),
            },
        )

    def resolve_dependencies(self, *, workflow_id: str, depends_on: list[str] | None = None) -> dict[str, Any]:
        if self.store.orch_workflows.get(workflow_id) is None:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        did = _id("orch_dep")
        return self.store.orch_dependencies.save(
            did,
            {
                "dependency_id": did,
                "workflow_id": workflow_id,
                "depends_on": depends_on or [],
                "resolved": True,
                "at": _now(),
            },
        )

    def execute(self, *, workflow_id: str, plan_id: str = "") -> dict[str, Any]:
        wf = self.store.orch_workflows.get(workflow_id)
        if wf is None:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        eid = _id("orch_exec")
        return self.store.orch_executions.save(
            eid,
            {
                "execution_id": eid,
                "workflow_id": workflow_id,
                "plan_id": plan_id,
                "status": "completed",
                "steps_completed": len(wf.get("steps") or []),
                "at": _now(),
            },
        )

    def schedule(self, *, workflow_id: str, cron: str = "0 * * * *") -> dict[str, Any]:
        if self.store.orch_workflows.get(workflow_id) is None:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        sid = _id("orch_sch")
        return self.store.orch_schedules.save(
            sid,
            {
                "schedule_id": sid,
                "workflow_id": workflow_id,
                "cron": cron,
                "status": "scheduled",
                "at": _now(),
            },
        )

    def retry(self, *, execution_id: str) -> dict[str, Any]:
        exe = self.store.orch_executions.get(execution_id)
        if exe is None:
            raise NotFoundError(f"execution not found: {execution_id}")
        rid = _id("orch_retry")
        return self.store.orch_retries.save(
            rid,
            {
                "retry_id": rid,
                "execution_id": execution_id,
                "status": "retried",
                "at": _now(),
            },
        )

    def rollback(self, *, execution_id: str, reason: str = "") -> dict[str, Any]:
        exe = self.store.orch_executions.get(execution_id)
        if exe is None:
            raise NotFoundError(f"execution not found: {execution_id}")
        rid = _id("orch_rb")
        return self.store.orch_rollbacks.save(
            rid,
            {
                "rollback_id": rid,
                "execution_id": execution_id,
                "reason": reason or "manual_rollback",
                "status": "rolled_back",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "workflows": self.store.orch_workflows.count(),
            "plans": self.store.orch_plans.count(),
            "queue": self.store.orch_queue.count(),
            "dependencies": self.store.orch_dependencies.count(),
            "executions": self.store.orch_executions.count(),
            "schedules": self.store.orch_schedules.count(),
            "retries": self.store.orch_retries.count(),
            "rollbacks": self.store.orch_rollbacks.count(),
            "kinds": self.workflow_kinds,
        }
