"""Task / Pipeline executors — backends for Hercules nodes."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from platform_hercules.core.models import ExecutionNode, ExecutorBackend

logger = logging.getLogger(__name__)

Handler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]] | dict[str, Any]]


class TaskExecutor:
    """Dispatches a single ExecutionNode to the right backend."""

    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}

    def register(self, name: str, handler: Handler) -> None:
        self._handlers[name] = handler

    async def execute_node(self, node: ExecutionNode, *, context: dict[str, Any]) -> dict[str, Any]:
        backend = node.backend
        payload = {**node.payload, **context}

        if backend == ExecutorBackend.PIPELINE or backend == ExecutorBackend.AI_PROVIDER:
            return await self._run_ai_pipeline(payload)
        if backend == ExecutorBackend.INTERNAL:
            return await self._run_internal(node.name, payload)
        if backend in (ExecutorBackend.HTTP, ExecutorBackend.REST):
            return await self._run_http(payload)
        if backend == ExecutorBackend.TELEGRAM:
            return {"status": "queued_telegram", "payload": payload}
        if backend == ExecutorBackend.WORKFLOW:
            return await self._run_workflow(payload)
        if backend == ExecutorBackend.EVENT_BUS:
            return {"status": "published", "event": payload.get("event", "hercules.task")}
        if backend == ExecutorBackend.N8N:
            return {"status": "n8n_handoff", "note": "Webhook handoff prepared"}
        if backend == ExecutorBackend.CRON:
            return {"status": "cron_registered", "payload": payload}
        if backend == ExecutorBackend.PYTHON:
            return await self._run_internal(node.name, payload)
        if backend == ExecutorBackend.NODE:
            return {"status": "node_bridge", "payload": payload}
        if backend == ExecutorBackend.WEBSOCKET:
            return {"status": "ws_push", "payload": payload}
        return {"status": "unsupported", "backend": backend.value}

    async def _run_internal(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        handler = self._handlers.get(name)
        if handler is None:
            # Default echo for unregistered internal jobs
            await asyncio.sleep(0)
            return {"status": "ok", "handler": name, "echo": payload}
        result = handler(payload)
        if asyncio.iscoroutine(result):
            return await result  # type: ignore[misc]
        return result  # type: ignore[return-value]

    async def _run_ai_pipeline(self, payload: dict[str, Any]) -> dict[str, Any]:
        from platform_ai.pipeline import unified_ai_pipeline
        from platform_ai.pipeline_models import AiChannel, AiTaskRequest

        req = AiTaskRequest(
            owner_id=str(payload.get("owner_id", "hercules")),
            modality=str(payload.get("modality", "text")),
            prompt=str(payload.get("prompt", "")),
            channel=str(payload.get("channel", AiChannel.AUTOMATION.value)),
            vertical=payload.get("vertical"),
            studio_id=payload.get("studio_id"),
            meta=dict(payload.get("meta") or {}),
            optimize_prompt=bool(payload.get("optimize_prompt", True)),
        )
        task = await unified_ai_pipeline.run(req)
        return {
            "status": task.status,
            "task_id": task.id,
            "result": task.result,
            "cost": task.cost_estimate,
            "via": "unified_ai_pipeline",
        }

    async def _run_http(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = payload.get("url")
        if not url:
            return {"status": "error", "error": "url required"}
        # Soft stub — avoid network in unit tests unless ADOS_HERCULES_HTTP=1
        import os

        if os.environ.get("ADOS_HERCULES_HTTP") != "1":
            return {"status": "http_sandbox", "url": url}
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    payload.get("method", "POST"),
                    url,
                    json=payload.get("body"),
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    text = await resp.text()
                    return {"status": "ok", "code": resp.status, "body": text[:2000]}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": str(exc)}

    async def _run_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            from platform_jobs.job_engine import job_engine

            job = await job_engine.enqueue(
                payload.get("handler", "hercules.workflow"),
                payload,
            )
            return {"status": "enqueued", "job_id": job.id, "via": "platform_jobs"}
        except Exception as exc:  # noqa: BLE001
            logger.debug("workflow bridge soft-fail: %s", exc)
            return {"status": "workflow_local", "payload": payload}


class PipelineExecutor:
    """Runs ExecutionGraph nodes in topological order."""

    def __init__(self, task_executor: TaskExecutor | None = None) -> None:
        self.tasks = task_executor or TaskExecutor()

    async def run_graph(
        self,
        nodes: list[ExecutionNode],
        *,
        context: dict[str, Any],
        on_node: Callable[[ExecutionNode, dict[str, Any]], Any] | None = None,
    ) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for node in nodes:
            out = await self.tasks.execute_node(node, context={**context, "node_results": results})
            results[node.id] = out
            if on_node:
                maybe = on_node(node, out)
                if asyncio.iscoroutine(maybe):
                    await maybe
        return results


task_executor = TaskExecutor()
pipeline_executor = PipelineExecutor(task_executor)
