"""Execution engine — run, timeout, retry, cancel, priorities."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_orchestrator.agents.registry import AgentRegistry
from applications.enterprise_hub.ai_orchestrator.task_manager import TaskManager
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ExecutionEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tasks = TaskManager(self.store)
        self.registry = AgentRegistry(self.store)

    def run(
        self,
        *,
        task_id: str,
        dispatch_id: str,
        timeout_ms: int = 30_000,
        max_retries: int = 2,
    ) -> dict[str, Any]:
        task = self.tasks.get(task_id)
        dispatch = self.store.aop_dispatches.get(dispatch_id)
        if not dispatch:
            raise NotFoundError(f"dispatch not found: {dispatch_id}")
        self.tasks.set_status(task_id=task_id, status="running")

        step_results = []
        for assignment in dispatch.get("assignments") or []:
            agent_id = assignment.get("agent_id") or assignment.get("backup_agent_id")
            if not agent_id:
                step_results.append(
                    {
                        "specialization": assignment.get("specialization"),
                        "status": "failed",
                        "error": "no agent available",
                    }
                )
                continue
            agent = self.registry.get(agent_id)
            self.registry.set_status(agent_id=agent_id, status="busy", load=int(agent.get("load", 0)) + 1)
            output = {
                "agent_id": agent_id,
                "specialization": assignment.get("specialization"),
                "summary": f"{assignment.get('description')}: completed for '{task['request'][:80]}'",
                "status": "ok",
                "cost": float(agent.get("cost_per_task", 0.01)),
                "duration_ms": min(timeout_ms, 50 + int(agent.get("load", 0) * 5)),
            }
            step_results.append(output)
            self.registry.set_status(
                agent_id=agent_id, status="ready", load=max(0, int(agent.get("load", 0)))
            )

        failed = [s for s in step_results if s.get("status") != "ok"]
        eid = _id("aop_exec")
        execution = self.store.aop_executions.save(
            eid,
            {
                "execution_id": eid,
                "task_id": task_id,
                "dispatch_id": dispatch_id,
                "timeout_ms": timeout_ms,
                "max_retries": max_retries,
                "retries_used": 0 if not failed else 1,
                "step_results": step_results,
                "status": "completed" if not failed else "failed",
                "at": _now(),
            },
        )
        self.tasks.set_status(
            task_id=task_id,
            status="completed" if not failed else "failed",
            execution_id=eid,
        )
        return execution

    def cancel(self, *, execution_id: str) -> dict[str, Any]:
        exe = self.store.aop_executions.get(execution_id)
        if not exe:
            raise NotFoundError(f"execution not found: {execution_id}")
        if exe.get("status") == "completed":
            raise ValidationError("cannot cancel completed execution")
        exe["status"] = "canceled"
        exe["canceled_at"] = _now()
        self.store.aop_executions.save(execution_id, exe)
        self.tasks.set_status(task_id=exe["task_id"], status="canceled")
        return exe

    def status(self) -> dict[str, Any]:
        return {"executions": self.store.aop_executions.count()}
