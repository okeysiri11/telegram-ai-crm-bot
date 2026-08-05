"""Workflow Runtime Service façade — Sprint 36.2."""

from __future__ import annotations

from typing import Any

from platform_workflow.registry import WorkflowRegistry, workflow_registry
from platform_workflow.runtime_engine import WorkflowRuntimeEngine, workflow_runtime
from platform_workflow.runtime_models import GraphStep, StepKind, WorkflowDefinition


DEMO_WORKFLOWS: list[dict[str, Any]] = [
    {
        "workflow_id": "wf_approval_pipeline",
        "name": "Approval Pipeline",
        "version": "1.0.0",
        "description": "Condition + parallel review demo",
        "variables": {"amount": 1000, "approved": True},
        "steps": [
            {"step_id": "start", "name": "Start", "kind": "start", "next": ["check"]},
            {
                "step_id": "check",
                "name": "Needs Approval",
                "kind": "condition",
                "condition": "vars.amount > 500",
                "when_true": "parallel_review",
                "when_false": "auto_approve",
            },
            {
                "step_id": "parallel_review",
                "name": "Parallel Review",
                "kind": "parallel",
                "branches": ["rev_a", "rev_b"],
                "join": "finalize",
            },
            {"step_id": "rev_a", "name": "Review A", "kind": "task", "action": "echo", "metadata": {"message": "A"}, "next": []},
            {"step_id": "rev_b", "name": "Review B", "kind": "task", "action": "echo", "metadata": {"message": "B"}, "next": []},
            {"step_id": "auto_approve", "name": "Auto Approve", "kind": "task", "action": "echo", "metadata": {"message": "auto"}, "next": ["finalize"]},
            {"step_id": "finalize", "name": "Finalize", "kind": "set_variable", "set_var": "done", "value": True, "next": ["end"]},
            {"step_id": "end", "name": "End", "kind": "end"},
        ],
        "start_step": "start",
        "tags": ["demo", "approval"],
    },
    {
        "workflow_id": "wf_loop_sum",
        "name": "Loop Accumulator",
        "version": "1.0.0",
        "description": "Loop over items and append results",
        "variables": {"items": [1, 2, 3], "items_out": []},
        "steps": [
            {"step_id": "start", "name": "Start", "kind": "start", "next": ["loop"]},
            {
                "step_id": "loop",
                "name": "For Each",
                "kind": "loop",
                "loop_over": "items",
                "loop_body": "body",
                "max_iterations": 10,
                "next": ["end"],
            },
            {"step_id": "body", "name": "Append", "kind": "task", "action": "append", "set_var": "items_out", "next": []},
            {"step_id": "end", "name": "End", "kind": "end"},
        ],
        "start_step": "start",
        "tags": ["demo", "loop"],
    },
]


class WorkflowRuntimeService:
    def __init__(
        self,
        registry: WorkflowRegistry | None = None,
        runtime: WorkflowRuntimeEngine | None = None,
    ) -> None:
        self.registry = registry or workflow_registry
        self.runtime = runtime or workflow_runtime
        self._seeded = False

    def reset(self) -> None:
        self.registry.reset()
        self.runtime.reset()
        self._seeded = False

    def ensure_seed(self) -> None:
        if self._seeded:
            return
        for item in DEMO_WORKFLOWS:
            if item["workflow_id"] not in getattr(self.registry, "_defs", {}):
                try:
                    self.registry.register(item)
                    self.registry.publish(item["workflow_id"])
                except ValueError:
                    pass
        self._seeded = True

    def status(self) -> dict[str, Any]:
        self.ensure_seed()
        return {
            "module": "platform_workflow",
            "sprint": "36.2",
            "sor": "platform_workflow.WorkflowEngine + WorkflowRuntimeEngine",
            "workflows": len(self.registry.list_workflows()),
            "runs": len(self.runtime.list_runs()),
            "scheduled": len(self.runtime._scheduled),
        }

    # registry
    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.ensure_seed()
        return self.registry.register(payload).to_dict()

    def list_workflows(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.ensure_seed()
        return [w.to_dict() for w in self.registry.list_workflows(**kwargs)]

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        self.ensure_seed()
        return self.registry.get(workflow_id).to_dict()

    def update_workflow(self, workflow_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        self.ensure_seed()
        return self.registry.update(workflow_id, patch).to_dict()

    def publish(self, workflow_id: str) -> dict[str, Any]:
        self.ensure_seed()
        return self.registry.publish(workflow_id).to_dict()

    def archive(self, workflow_id: str) -> dict[str, Any]:
        self.ensure_seed()
        return self.registry.archive(workflow_id).to_dict()

    def versions(self, workflow_id: str) -> list[dict[str, Any]]:
        self.ensure_seed()
        return [v.to_dict() for v in self.registry.versions(workflow_id)]

    # runtime
    async def execute(self, workflow_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self.ensure_seed()
        payload = payload or {}
        input_vars = dict(payload.get("variables") or payload.get("input") or payload.get("vars") or {})
        if payload.get("use_context_engine"):
            try:
                from platform_memory.service import context_engine_service

                ctx = await context_engine_service.for_workflow(
                    {
                        "query": str(payload.get("query") or workflow_id),
                        "principal": str(payload.get("actor") or "system"),
                        "session_id": payload.get("context_session_id"),
                    }
                )
                input_vars = {
                    **input_vars,
                    **(ctx.get("vars") or {}),
                    "context_memory": (ctx.get("memory") or {}),
                }
            except Exception:
                pass
        if payload.get("use_project_memory"):
            try:
                from platform_memory.project_memory_service import project_memory_service

                mem = await project_memory_service.for_workflow(
                    {
                        "query": str(payload.get("query") or workflow_id),
                        "workflow_id": workflow_id,
                        "project_id": payload.get("project_id"),
                        "write": payload.get("memory_write"),
                    }
                )
                input_vars = {
                    **input_vars,
                    "project_memory": (mem.get("memory") or {}),
                    "project_memory_hits": mem.get("hits") or [],
                }
            except Exception:
                pass
        run = await self.runtime.execute(
            workflow_id,
            input_vars=input_vars,
            mode=str(payload.get("mode") or "sync"),
            timeout_sec=payload.get("timeout_sec"),
            schedule_at=payload.get("schedule_at"),
            actor=str(payload.get("actor") or "system"),
        )
        return run.to_dict()

    def list_runs(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.ensure_seed()
        return [r.to_dict() for r in self.runtime.list_runs(**kwargs)]

    def get_run(self, run_id: str) -> dict[str, Any]:
        self.ensure_seed()
        return self.runtime.get_run(run_id).to_dict()

    async def cancel(self, run_id: str) -> dict[str, Any]:
        return (await self.runtime.cancel(run_id)).to_dict()

    async def retry(self, run_id: str, *, actor: str = "system") -> dict[str, Any]:
        return (await self.runtime.retry(run_id, actor=actor)).to_dict()

    async def rollback(self, run_id: str, *, actor: str = "system") -> dict[str, Any]:
        return (await self.runtime.rollback(run_id, actor=actor)).to_dict()

    async def process_scheduled(self) -> dict[str, Any]:
        n = await self.runtime.process_scheduled()
        return {"processed": n}

    def monitoring(self) -> dict[str, Any]:
        self.ensure_seed()
        runs = self.runtime.list_runs(limit=500)
        by_status: dict[str, int] = {}
        for r in runs:
            key = r.status.value if hasattr(r.status, "value") else str(r.status)
            by_status[key] = by_status.get(key, 0) + 1
        return {
            "workflows": len(self.registry.list_workflows()),
            "runs": len(runs),
            "by_status": by_status,
            "scheduled": len(self.runtime._scheduled),
            "async_active": len(self.runtime._async_tasks),
        }


workflow_runtime_service = WorkflowRuntimeService()
