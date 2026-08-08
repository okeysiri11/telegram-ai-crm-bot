"""Epic 45.3 — Universal Workflow Engine (executes JSON workflows via Hercules).

Note: legacy platform_workflows.workflow_engine remains for YAML SoR adapter.
This engine is the Universal Automation runtime for Epic 45.3.
"""
from __future__ import annotations
from typing import Any
from platform_workflows.approval_engine import approval_engine
from platform_workflows.job_runner import job_runner
from platform_workflows.orchestrator import workflow_orchestrator
from platform_workflows.ua_store import WorkflowRun, new_id, ua_store
from platform_workflows.workflow_events import WorkflowEvent, workflow_events
from platform_workflows.workflow_history import workflow_history
from platform_workflows.workflow_logger import workflow_logger

class UniversalWorkflowEngine:
    VERSION = "45.3.0"
    def start(self, owner_id: str, workflow_id: str, *, channel: str = "web", auto_approve: bool | None = None) -> dict[str, Any]:
        spec = ua_store.workflows.get(workflow_id)
        if not spec or spec.owner_id != owner_id:
            return {"error": "workflow_not_found"}
        blocks = workflow_orchestrator.merge_duplicates(list(spec.blocks))
        run = WorkflowRun(
            id=new_id("run"), workflow_id=workflow_id, owner_id=owner_id, status="running",
            steps=[{"id": b.get("id"), "title": b.get("title"), "type": b.get("type"), "kind": b.get("kind"), "status": "pending", "parallel_group": b.get("parallel_group")} for b in blocks],
            channel=channel, via_hercules=True,
        )
        ua_store.runs[run.id] = run
        workflow_events.emit(WorkflowEvent(type="run_started", owner_id=owner_id, workflow_id=workflow_id, run_id=run.id))
        workflow_logger.log(run.id, "Запуск через Hercules Runtime")
        return self._advance(run.id, auto_approve=auto_approve)
    def _advance(self, run_id: str, *, auto_approve: bool | None = None) -> dict[str, Any]:
        run = ua_store.runs.get(run_id)
        if not run or run.status in ("completed", "failed", "cancelled"):
            return run.to_dict() if run else {"error": "not_found"}
        spec = ua_store.workflows.get(run.workflow_id)
        blocks = list(spec.blocks) if spec else []
        blocks = workflow_orchestrator.merge_duplicates(blocks)
        waves = workflow_orchestrator.schedule_waves(blocks)
        # find current wave index from current_step
        flat_index = run.current_step
        # execute remaining from flat_index
        executed = 0
        for wave in waves:
            if executed + len(wave) <= flat_index:
                executed += len(wave)
                continue
            # skip already done items in wave
            pending = []
            for b in wave:
                if executed < flat_index:
                    executed += 1
                    continue
                pending.append(b)
            if not pending:
                continue
            need_approval = approval_engine.requires_approval(run.owner_id) if auto_approve is None else (not auto_approve)
            # approval on generation/approval blocks in Human Mode
            for b in pending:
                if need_approval and (b.get("type") in ("generation", "approval") or b.get("kind") == "generation"):
                    preview = f"Промежуточный результат: {b.get('title')}"
                    approval_engine.request(run.id, step=b, preview=preview)
                    ua_store.runs[run.id] = run
                    return run.to_dict()
            def exec_one(b: dict[str, Any]) -> dict[str, Any]:
                if b.get("type") in ("start", "finish"):
                    return {"ok": True, "output": b.get("title"), "via_hercules": True, "cost": 0, "model": None}
                if b.get("type") == "memory" or b.get("kind") == "memory":
                    self._save_memory(run, b)
                    return {"ok": True, "output": "Сохранено в Continuous Memory", "via_hercules": True, "cost": 0.0, "model": None}
                return job_runner.execute_step(b, owner_id=run.owner_id, context={"run_id": run.id})
            wave_result = workflow_orchestrator.run_wave(pending, exec_one)
            for bid, res in (wave_result.get("results") or {}).items():
                for s in run.steps:
                    if s.get("id") == bid:
                        s["status"] = "completed" if res.get("ok") else "failed"
                        s["result"] = res
                if res.get("model"):
                    run.models.append(res["model"])
                run.cost += float(res.get("cost") or 0)
                workflow_logger.log(run.id, f"{bid}: {res.get('output')}")
            if wave_result.get("errors"):
                run.status = "failed"
                run.result["errors"] = wave_result["errors"]
                ua_store.runs[run.id] = run
                workflow_history.record({"owner_id": run.owner_id, "workflow_id": run.workflow_id, "run_id": run.id, "status": "failed"})
                return run.to_dict()
            run.current_step = executed + len(pending)
            executed = run.current_step
            ua_store.runs[run.id] = run
        run.status = "completed"
        run.result["summary_ru"] = "Workflow завершён"
        run.result["cost"] = run.cost
        ua_store.runs[run.id] = run
        workflow_history.record({"owner_id": run.owner_id, "workflow_id": run.workflow_id, "run_id": run.id, "status": "completed", "cost": run.cost})
        workflow_events.emit(WorkflowEvent(type="run_completed", owner_id=run.owner_id, workflow_id=run.workflow_id, run_id=run.id, payload={"cost": run.cost}))
        self._save_memory(run, {"title": "Workflow result"})
        return run.to_dict()
    def _save_memory(self, run: WorkflowRun, step: dict[str, Any]) -> None:
        try:
            from platform_memory.memory_manager import memory_manager
            memory_manager.save(
                run.owner_id,
                title=f"WF {run.workflow_id}: {step.get('title') or 'result'}",
                content=str(run.result.get("summary_ru") or step.get("title") or run.id),
                level="working",
                kind="workflow",
                channel=run.channel,
                tags=["workflow", "automation"],
                metadata={"run_id": run.id, "workflow_id": run.workflow_id},
            )
        except Exception:
            pass
    def continue_after_approval(self, run_id: str, owner_id: str) -> dict[str, Any]:
        approved = approval_engine.approve(run_id, owner_id)
        if approved.get("error"):
            return approved
        # mark current pending generation as approved and continue without re-asking
        return self._advance(run_id, auto_approve=True)
    def cancel(self, run_id: str, owner_id: str) -> dict[str, Any]:
        run = ua_store.runs.get(run_id)
        if not run or run.owner_id != owner_id:
            return {"error": "not_found"}
        run.status = "cancelled"
        ua_store.runs[run_id] = run
        return run.to_dict()
    def status(self, run_id: str) -> dict[str, Any] | None:
        run = ua_store.runs.get(run_id)
        return run.to_dict() if run else None
    def monitor(self, run_id: str) -> dict[str, Any] | None:
        run = ua_store.runs.get(run_id)
        if not run:
            return None
        d = run.to_dict()
        d["monitor"] = {
            "step_label": d["step_label"],
            "current_action": (run.steps[run.current_step]["title"] if run.current_step < len(run.steps) else "завершено"),
            "active_ai": run.models[-1] if run.models else None,
            "duration": run.updated_at - run.created_at,
            "cost": run.cost,
            "models": run.models,
            "logs": run.logs[-20:],
            "via_hercules": True,
        }
        return d

universal_workflow_engine = UniversalWorkflowEngine()
