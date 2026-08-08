"""Hercules orchestrator — plan → schedule → execute → store."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from platform_hercules.cache.cache import hercules_cache
from platform_hercules.core.models import (
    ExecutionContext,
    ExecutionPlan,
    ExecutionState,
    ExecutorBackend,
    HerculesJob,
    QueueKind,
    TaskLifecycle,
)
from platform_hercules.core.resources import resource_manager
from platform_hercules.executor.executor import pipeline_executor
from platform_hercules.memory.memory import hercules_memory
from platform_hercules.metrics.metrics import hercules_metrics
from platform_hercules.queue.queue import hercules_queue
from platform_hercules.scheduler.scheduler import hercules_scheduler
from platform_hercules.security.security import hercules_security
from platform_hercules.telemetry.telemetry import hercules_telemetry
from platform_hercules.workers.registry import worker_registry

logger = logging.getLogger(__name__)


class HerculesOrchestrator:
    """Receives work from Concierge / Telegram / API / Agents and runs ExecutionPlans."""

    def __init__(self) -> None:
        self._jobs: dict[str, HerculesJob] = {}

    def get(self, job_id: str) -> HerculesJob | None:
        return self._jobs.get(job_id)

    def list_jobs(self, *, limit: int = 50) -> list[HerculesJob]:
        jobs = sorted(self._jobs.values(), key=lambda j: j.plan.created_at, reverse=True)
        return jobs[:limit]

    def cancel(self, job_id: str) -> HerculesJob | None:
        job = self._jobs.get(job_id)
        if not job:
            return None
        if job.state.lifecycle in (TaskLifecycle.SUCCEEDED, TaskLifecycle.FAILED, TaskLifecycle.CANCELLED):
            return job
        job.state.lifecycle = TaskLifecycle.CANCELLED
        job.state.finished_at = time.time()
        resource_manager.release(job.id)
        hercules_security.record("cancel", job.plan.context.owner_id, job_id)
        return job

    async def submit(self, plan: ExecutionPlan) -> HerculesJob:
        actor = plan.context.owner_id
        if not hercules_security.check_rate(actor):
            raise RuntimeError("Превышен лимит запросов Hercules")

        job_id = str(uuid.uuid4())
        state = ExecutionState(plan_id=plan.id, lifecycle=TaskLifecycle.QUEUED, queue=QueueKind.TASK)
        job = HerculesJob(id=job_id, plan=plan, state=state)
        self._jobs[job_id] = job

        need_gpu = any(n.gpu_required for n in plan.graph.nodes)
        lease = resource_manager.try_acquire(lease_id=job_id, gpu=need_gpu)
        if lease is None:
            job.state.lifecycle = TaskLifecycle.WAITING
            hercules_queue.enqueue(job_id, "background", priority=plan.context.priority)
            return job

        queue = plan.graph.nodes[0].queue if plan.graph.nodes else QueueKind.TASK
        hercules_scheduler.enqueue(job_id, queue=queue, priority=plan.context.priority)
        hercules_queue.enqueue(job_id, queue.value, priority=plan.context.priority)

        worker = worker_registry.pick(
            "llm" if queue == QueueKind.AI else "universal",
            need_gpu=need_gpu,
        )
        if worker:
            job.state.worker_id = worker.id

        return await self._execute(job)

    async def _execute(self, job: HerculesJob) -> HerculesJob:
        hercules_metrics.on_start()
        job.state.lifecycle = TaskLifecycle.RUNNING
        job.state.started_at = time.time()
        hercules_telemetry.log("job_start", job_id=job.id, label=job.plan.label)

        ctx = {
            "owner_id": job.plan.context.owner_id,
            "tenant_id": job.plan.context.tenant_id,
            "channel": job.plan.context.channel,
            "vertical": job.plan.context.vertical,
            "session_id": job.plan.context.session_id,
            **job.plan.context.meta,
        }

        # Prompt cache short-circuit for identical AI prompts
        for node in job.plan.graph.nodes:
            if node.backend in (ExecutorBackend.PIPELINE, ExecutorBackend.AI_PROVIDER):
                prompt = str(node.payload.get("prompt", ""))
                cached = hercules_cache.get("prompt", prompt)
                if cached:
                    job.state.node_results[node.id] = cached
                    job.state.result = cached
                    job.state.lifecycle = TaskLifecycle.SUCCEEDED
                    job.state.progress = 1.0
                    job.state.finished_at = time.time()
                    hercules_metrics.on_success(job.state.duration_sec() or 0.0)
                    resource_manager.release(job.id)
                    return job

        try:
            order = job.plan.graph.topological_order()
            results = await pipeline_executor.run_graph(order, context=ctx)
            job.state.node_results = results
            job.state.result = results
            job.state.lifecycle = TaskLifecycle.SUCCEEDED
            job.state.progress = 1.0
            cost = 0.0
            for r in results.values():
                if isinstance(r, dict):
                    cost += float(r.get("cost") or 0)
                    if r.get("status") == "ok" or r.get("task_id"):
                        prompt = ""
                        for n in order:
                            if n.id in results:
                                prompt = str(n.payload.get("prompt", ""))
                                break
                        if prompt:
                            hercules_cache.set("prompt", prompt, r)
            job.state.cost = cost
            hercules_memory.put(f"job:{job.id}", results, kind="task")
            hercules_metrics.on_success(job.state.duration_sec() or 0.0, cost=cost)
            hercules_security.record("complete", job.plan.context.owner_id, job.id)
        except Exception as exc:  # noqa: BLE001
            job.state.lifecycle = TaskLifecycle.FAILED
            job.state.error = str(exc)
            hercules_metrics.on_failure(job.state.duration_sec() or 0.0)
            hercules_telemetry.report_crash(str(exc), context={"job_id": job.id})
        finally:
            job.state.finished_at = time.time()
            resource_manager.release(job.id)

        return job

    async def submit_ai(
        self,
        context: ExecutionContext,
        *,
        prompt: str,
        modality: str = "text",
        vertical: str | None = None,
    ) -> HerculesJob:
        plan = ExecutionPlan.from_single(
            context,
            name="ai_generate",
            backend=ExecutorBackend.PIPELINE,
            queue=QueueKind.AI,
            payload={
                "prompt": prompt,
                "modality": modality,
                "owner_id": context.owner_id,
                "channel": context.channel,
                "vertical": vertical or context.vertical,
            },
            gpu_required=modality in ("image", "video"),
        )
        return await self.submit(plan)

    async def retry(self, job_id: str) -> HerculesJob:
        old = self._jobs.get(job_id)
        if not old:
            raise KeyError(job_id)
        hercules_metrics.on_retry()
        return await self.submit(old.plan)


hercules_orchestrator = HerculesOrchestrator()
