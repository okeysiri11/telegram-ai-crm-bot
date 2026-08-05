"""Graph Workflow Runtime Engine — conditions, loops, parallel, retry, rollback.

Part of platform_workflow SoR (Sprint 36.2). Not a second engine package.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

from platform_workflow.registry import WorkflowRegistry, workflow_registry
from platform_workflow.runtime_models import (
    GraphStep,
    RegistryStatus,
    RunStatus,
    RuntimeContext,
    StepKind,
    StepRunRecord,
    StepStatus,
    WorkflowDefinition,
    WorkflowRun,
    eval_expression,
)

logger = logging.getLogger(__name__)


class WorkflowRuntimeEngine:
    def __init__(self, registry: WorkflowRegistry | None = None) -> None:
        self.registry = registry or workflow_registry
        self._runs: dict[str, WorkflowRun] = {}
        self._cancelled: set[str] = set()
        self._scheduled: list[WorkflowRun] = []
        self._async_tasks: dict[str, asyncio.Task] = {}

    def reset(self) -> None:
        for task in self._async_tasks.values():
            task.cancel()
        self._async_tasks.clear()
        self._runs.clear()
        self._cancelled.clear()
        self._scheduled.clear()

    def get_run(self, run_id: str) -> WorkflowRun:
        run = self._runs.get(run_id)
        if run is None:
            raise KeyError(f"run not found: {run_id}")
        return run

    def list_runs(self, *, workflow_id: str | None = None, limit: int = 100) -> list[WorkflowRun]:
        rows = list(self._runs.values())
        if workflow_id:
            rows = [r for r in rows if r.workflow_id == workflow_id]
        rows.sort(key=lambda r: r.created_at)
        return rows[-limit:]

    async def execute(
        self,
        workflow_id: str,
        *,
        input_vars: dict[str, Any] | None = None,
        mode: str = "sync",
        timeout_sec: float | None = None,
        schedule_at: float | None = None,
        actor: str = "system",
    ) -> WorkflowRun:
        wf = self.registry.get(workflow_id)
        if wf.status == RegistryStatus.ARCHIVED:
            raise ValueError("cannot execute archived workflow")
        # allow draft for testing; prefer published in production
        ctx = RuntimeContext(vars={**(wf.variables or {}), **(input_vars or {})})
        ctx.meta["actor"] = actor
        run = WorkflowRun(
            run_id=f"run_{uuid.uuid4().hex[:12]}",
            workflow_id=wf.workflow_id,
            version=wf.version,
            mode=mode,
            context=ctx,
            timeout_sec=float(timeout_sec if timeout_sec is not None else 120.0),
            scheduled_at=schedule_at,
        )
        self._runs[run.run_id] = run
        self._log(run, "run_created", f"mode={mode}")

        if schedule_at and schedule_at > time.time():
            run.status = RunStatus.SCHEDULED
            run.mode = "scheduled"
            self._scheduled.append(run)
            self._log(run, "scheduled", f"at={schedule_at}")
            await self._emit(run, "workflow.scheduled")
            return run

        if mode == "async":
            task = asyncio.create_task(self._run_safe(wf, run))
            self._async_tasks[run.run_id] = task
            return run

        await self._run_safe(wf, run)
        return run

    async def process_scheduled(self, *, now: float | None = None) -> int:
        now = now if now is not None else time.time()
        due = [r for r in self._scheduled if (r.scheduled_at or 0) <= now]
        self._scheduled = [r for r in self._scheduled if (r.scheduled_at or 0) > now]
        for run in due:
            wf = self.registry.get(run.workflow_id)
            run.mode = "sync"
            await self._run_safe(wf, run)
        return len(due)

    async def cancel(self, run_id: str) -> WorkflowRun:
        run = self.get_run(run_id)
        self._cancelled.add(run_id)
        task = self._async_tasks.pop(run_id, None)
        if task:
            task.cancel()
        if run.status in {RunStatus.RUNNING, RunStatus.PENDING, RunStatus.SCHEDULED}:
            run.status = RunStatus.CANCELLED
            run.finished_at = time.time()
            self._log(run, "cancelled", "by request")
            await self._emit(run, "workflow.cancelled")
        return run

    async def retry(self, run_id: str, *, actor: str = "system") -> WorkflowRun:
        prev = self.get_run(run_id)
        return await self.execute(
            prev.workflow_id,
            input_vars=dict(prev.context.vars),
            mode="sync",
            timeout_sec=prev.timeout_sec,
            actor=actor,
        )

    async def rollback(self, run_id: str, *, actor: str = "system") -> WorkflowRun:
        prev = self.get_run(run_id)
        wf = self.registry.get(prev.workflow_id)
        run = WorkflowRun(
            run_id=f"run_{uuid.uuid4().hex[:12]}",
            workflow_id=wf.workflow_id,
            version=wf.version,
            mode="sync",
            context=RuntimeContext.from_dict(prev.context.to_dict()),
            rollback_of=run_id,
            status=RunStatus.ROLLING_BACK,
            timeout_sec=prev.timeout_sec,
        )
        run.context.meta["actor"] = actor
        self._runs[run.run_id] = run
        run.started_at = time.time()
        self._log(run, "rollback_start", f"of={run_id}")

        # execute compensate steps in reverse order of completed steps
        step_map = wf.step_map()
        completed = [s for s in prev.steps if s.status == StepStatus.COMPLETED]
        for step_rec in reversed(completed):
            step = step_map.get(step_rec.step_id)
            if not step or not step.compensate:
                continue
            comp = step_map.get(step.compensate)
            if not comp:
                continue
            await self._execute_step(run, wf, comp)
        run.status = RunStatus.ROLLED_BACK
        run.finished_at = time.time()
        self._checkpoint(run, "rolled_back")
        await self._emit(run, "workflow.rolled_back")
        return run

    async def _run_safe(self, wf: WorkflowDefinition, run: WorkflowRun) -> None:
        try:
            await self._execute_graph(wf, run)
        except asyncio.CancelledError:
            run.status = RunStatus.CANCELLED
            run.finished_at = time.time()
            self._log(run, "cancelled", "task cancelled")
        except Exception as exc:
            run.status = RunStatus.FAILED
            run.error = str(exc)
            run.finished_at = time.time()
            self._log(run, "failed", str(exc))
            await self._emit(run, "workflow.failed")
        finally:
            self._async_tasks.pop(run.run_id, None)

    async def _execute_graph(self, wf: WorkflowDefinition, run: WorkflowRun) -> None:
        run.status = RunStatus.RUNNING
        run.started_at = time.time()
        self._log(run, "started", wf.name)
        await self._emit(run, "workflow.started")
        self._checkpoint(run, "started")

        deadline = time.time() + run.timeout_sec
        start_id = wf.start_step or (wf.steps[0].step_id if wf.steps else None)
        if not start_id:
            raise ValueError("workflow has no steps")

        await self._walk(wf, run, start_id, deadline)

        if run.run_id in self._cancelled:
            run.status = RunStatus.CANCELLED
        elif run.status == RunStatus.RUNNING:
            run.status = RunStatus.COMPLETED
        run.finished_at = time.time()
        self._checkpoint(run, run.status.value)
        event = "workflow.completed" if run.status == RunStatus.COMPLETED else f"workflow.{run.status.value}"
        await self._emit(run, event)
        self._log(run, "finished", run.status.value)

    async def _walk(
        self,
        wf: WorkflowDefinition,
        run: WorkflowRun,
        step_id: str | None,
        deadline: float,
        *,
        visited_guard: int = 0,
    ) -> None:
        step_map = wf.step_map()
        current = step_id
        guard = visited_guard
        while current:
            if run.run_id in self._cancelled:
                run.status = RunStatus.CANCELLED
                return
            if time.time() > deadline:
                run.status = RunStatus.TIMED_OUT
                run.error = "execution timed out"
                self._log(run, "timeout", current)
                return
            guard += 1
            if guard > 10_000:
                raise RuntimeError("execution guard exceeded (possible infinite loop)")

            step = step_map.get(current)
            if step is None:
                raise KeyError(f"step not found: {current}")

            if step.kind == StepKind.END:
                await self._execute_step(run, wf, step)
                return

            if step.kind == StepKind.CONDITION:
                await self._execute_step(run, wf, step)
                truthy = bool(eval_expression(step.condition or "false", run.context))
                current = step.when_true if truthy else step.when_false
                if not current and step.next:
                    current = step.next[0]
                continue

            if step.kind == StepKind.LOOP:
                await self._execute_step(run, wf, step)
                items = run.context.vars.get(step.loop_over or "", [])
                if not isinstance(items, list):
                    items = list(items) if items else []
                body = step.loop_body or (step.next[0] if step.next else None)
                for i, item in enumerate(items[: step.max_iterations]):
                    run.context.vars["_loop_index"] = i
                    run.context.vars["_loop_item"] = item
                    if body:
                        await self._walk(wf, run, body, deadline, visited_guard=guard)
                    if run.status in {RunStatus.FAILED, RunStatus.CANCELLED, RunStatus.TIMED_OUT}:
                        return
                # after loop, continue to join/next excluding body
                nxt = [n for n in step.next if n != body]
                current = nxt[0] if nxt else None
                continue

            if step.kind == StepKind.PARALLEL:
                await self._execute_step(run, wf, step)
                branches = step.branches or list(step.next)
                join = step.join
                results = await asyncio.gather(
                    *[self._walk_branch(wf, run, b, deadline) for b in branches],
                    return_exceptions=True,
                )
                for r in results:
                    if isinstance(r, Exception):
                        run.status = RunStatus.FAILED
                        run.error = str(r)
                        return
                current = join
                continue

            await self._execute_step(run, wf, step)
            if run.status == RunStatus.FAILED:
                return
            current = step.next[0] if step.next else None

    async def _walk_branch(
        self,
        wf: WorkflowDefinition,
        run: WorkflowRun,
        step_id: str,
        deadline: float,
    ) -> None:
        # isolate temp for branch
        snapshot_temp = dict(run.context.temp)
        try:
            await self._walk(wf, run, step_id, deadline)
        finally:
            run.context.temp = snapshot_temp

    async def _execute_step(self, run: WorkflowRun, wf: WorkflowDefinition, step: GraphStep) -> StepRunRecord:
        rec = StepRunRecord(
            step_id=step.step_id,
            name=step.name,
            kind=step.kind.value if isinstance(step.kind, StepKind) else str(step.kind),
            status=StepStatus.RUNNING,
            started_at=time.time(),
        )
        run.steps.append(rec)
        self._log(run, "step_start", step.step_id)
        attempt = 0
        last_error: str | None = None
        while attempt <= step.max_retries:
            attempt += 1
            rec.attempt = attempt
            try:
                if step.timeout_sec > 0:
                    await asyncio.wait_for(self._run_step_body(run, step), timeout=step.timeout_sec)
                else:
                    await self._run_step_body(run, step)
                rec.status = StepStatus.COMPLETED
                rec.finished_at = time.time()
                rec.duration_ms = (rec.finished_at - (rec.started_at or rec.finished_at)) * 1000
                self._checkpoint(run, f"step:{step.step_id}")
                self._log(run, "step_ok", step.step_id)
                await self._emit(run, "workflow.step.completed", step_id=step.step_id)
                return rec
            except Exception as exc:
                last_error = str(exc)
                self._log(run, "step_retry", f"{step.step_id}:{exc}")
                if attempt <= step.max_retries:
                    await asyncio.sleep(0.01 * attempt)
                    continue
                break
        rec.status = StepStatus.FAILED
        rec.error = last_error
        rec.finished_at = time.time()
        run.status = RunStatus.FAILED
        run.error = last_error
        self._log(run, "step_failed", f"{step.step_id}:{last_error}")
        await self._emit(run, "workflow.step.failed", step_id=step.step_id, error=last_error)
        return rec

    async def _run_step_body(self, run: WorkflowRun, step: GraphStep) -> None:
        kind = step.kind
        if kind == StepKind.START:
            run.context.outputs["started"] = True
            return
        if kind == StepKind.END:
            run.context.outputs["ended"] = True
            return
        if kind == StepKind.DELAY:
            await asyncio.sleep(max(0.0, step.delay_sec))
            return
        if kind == StepKind.SET_VARIABLE or kind == StepKind.EXPRESSIONS:
            value = step.value
            if step.expression:
                value = eval_expression(step.expression, run.context)
            if step.set_var:
                run.context.vars[step.set_var] = value
            run.context.outputs[step.step_id] = value
            return
        if kind == StepKind.CONDITION:
            run.context.temp["last_condition"] = bool(eval_expression(step.condition or "false", run.context))
            return
        if kind == StepKind.LOOP:
            return
        if kind == StepKind.PARALLEL:
            return
        if kind == StepKind.ROLLBACK:
            return
        # TASK / default action
        action = step.action or "noop"
        if action == "fail":
            raise RuntimeError(step.metadata.get("error") or "task failed")
        if action == "echo":
            run.context.outputs[step.step_id] = {
                "echo": step.metadata.get("message") or run.context.vars,
            }
            return
        if action == "add":
            a = float(run.context.vars.get("a", 0))
            b = float(run.context.vars.get("b", 0))
            run.context.vars["sum"] = a + b
            run.context.outputs[step.step_id] = {"sum": a + b}
            return
        if action == "append":
            key = step.set_var or "items"
            run.context.vars.setdefault(key, [])
            if not isinstance(run.context.vars[key], list):
                run.context.vars[key] = []
            run.context.vars[key].append(step.value if step.value is not None else run.context.vars.get("_loop_item"))
            return
        # generic success
        run.context.outputs[step.step_id] = {"action": action, "ok": True}

    def _checkpoint(self, run: WorkflowRun, label: str) -> None:
        run.checkpoints.append(
            {
                "checkpoint_id": f"cp_{uuid.uuid4().hex[:10]}",
                "label": label,
                "at": time.time(),
                "status": run.status.value if isinstance(run.status, RunStatus) else run.status,
                "vars": dict(run.context.vars),
            }
        )

    def _log(self, run: WorkflowRun, event: str, message: str) -> None:
        run.logs.append({"at": time.time(), "event": event, "message": message})

    async def _emit(self, run: WorkflowRun, event_type: str, **extra: Any) -> None:
        try:
            from platform_enterprise_event_bus import enterprise_event_bus

            await enterprise_event_bus.publish(
                {
                    "event_type": event_type,
                    "category": "workflow",
                    "topic": "workflow",
                    "source_service": "svc_workflow_runtime",
                    "payload": {
                        "run_id": run.run_id,
                        "workflow_id": run.workflow_id,
                        "status": run.status.value if isinstance(run.status, RunStatus) else run.status,
                        **extra,
                    },
                },
                actor="workflow_runtime",
                bridge=True,
            )
        except Exception:
            logger.debug("workflow event emit skipped", exc_info=True)


workflow_runtime = WorkflowRuntimeEngine()
