# PlatformOrchestrator — central execution layer for all AI agents.

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from platform_orchestrator.agent_registry import AgentRegistry, agent_registry
from platform_orchestrator.capability_routing import CapabilityRouter, capability_router
from platform_orchestrator.config import DEFAULT_ORCHESTRATOR_CONFIG, OrchestratorConfig, RoutingPolicy
from platform_orchestrator.exceptions import (
    AgentExecutionError,
    OrchestratorError,
    TaskCancelledError,
    TaskRetryExhaustedError,
    TaskTimeoutError,
    TaskValidationError,
)
from platform_orchestrator.message_bus import AgentMessageBus, agent_message_bus
from platform_orchestrator.metrics import OrchestratorMetrics, orchestrator_metrics
from platform_orchestrator.models import (
    AgentContext,
    AgentMessage,
    MessageType,
    RoutingDecision,
    TaskRequest,
    TaskResult,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class PlatformOrchestrator:
    """Provider-independent multi-agent orchestration engine."""

    def __init__(
        self,
        *,
        registry: AgentRegistry | None = None,
        router: CapabilityRouter | None = None,
        message_bus: AgentMessageBus | None = None,
        metrics: OrchestratorMetrics | None = None,
        config: OrchestratorConfig | None = None,
    ) -> None:
        self._registry = registry or agent_registry
        self._router = router or CapabilityRouter(self._registry)
        self._message_bus = message_bus or agent_message_bus
        self._metrics = metrics or orchestrator_metrics
        self._config = config or DEFAULT_ORCHESTRATOR_CONFIG
        self._initialized = False
        self._running_tasks: dict[str, asyncio.Task[TaskResult]] = {}
        self._cancel_flags: set[str] = set()
        self._queue: asyncio.Queue[TaskRequest] = asyncio.Queue(maxsize=self._config.max_queue_length)

    def reset(self) -> None:
        self._initialized = False
        self._running_tasks.clear()
        self._cancel_flags.clear()
        self._queue = asyncio.Queue(maxsize=self._config.max_queue_length)
        self._registry.reset()
        self._message_bus.reset()
        self._metrics.reset()

    @property
    def registry(self) -> AgentRegistry:
        return self._registry

    @property
    def router(self) -> CapabilityRouter:
        return self._router

    @property
    def message_bus(self) -> AgentMessageBus:
        return self._message_bus

    @property
    def metrics(self) -> OrchestratorMetrics:
        return self._metrics

    async def initialize(self, context: AgentContext | None = None) -> None:
        ctx = context or AgentContext()
        for meta in self._registry.list():
            agent = self._registry.get(meta.id)
            await agent.initialize(ctx)
        self._wire_message_handlers()
        self._initialized = True
        logger.info("orchestrator_initialized agents=%s", len(self._registry.list()))

    def _wire_message_handlers(self) -> None:
        async def _handle_request(message: AgentMessage) -> None:
            if not message.target_agent_id:
                return
            try:
                agent = self._registry.get(message.target_agent_id)
            except OrchestratorError:
                return
            task = TaskRequest(
                capability=str(message.payload.get("capability", "inter_agent")),
                payload=dict(message.payload),
                task_id=message.correlation_id or message.message_id,
            )
            try:
                result = await agent.execute(task)
                await self._message_bus.respond(message, {"status": result.status.value, "output": result.output})
            except Exception as exc:
                await self._message_bus.respond(message, {"status": "failed", "error": str(exc)})

        self._message_bus.subscribe(MessageType.REQUEST, _handle_request)

    async def shutdown(self) -> None:
        for meta in self._registry.list():
            await self._registry.get(meta.id).shutdown()
        self._initialized = False
        logger.info("orchestrator_shutdown")

    def execute(self, task: TaskRequest) -> TaskResult:
        """Synchronous execution wrapper — use execute_async inside async code."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.execute_async(task))
        raise RuntimeError("Use execute_async() from an async context")

    async def execute_async(self, task: TaskRequest) -> TaskResult:
        if not self._initialized:
            await self.initialize(task.context)

        self._metrics.set_queue_length(self._queue.qsize() + len(self._running_tasks))
        started = time.monotonic()
        retries = 0
        max_retries = task.max_retries if task.max_retries is not None else self._config.max_retries
        timeout = task.timeout_seconds if task.timeout_seconds is not None else self._config.default_timeout_seconds
        preserved_context = task.context.as_dict()
        last_error = ""

        routing_decision: RoutingDecision | None = None
        agent_id = ""

        while retries <= max_retries:
            if task.task_id in self._cancel_flags:
                self._cancel_flags.discard(task.task_id)
                result = self._build_result(
                    task,
                    agent_id=agent_id or "unknown",
                    status=TaskStatus.CANCELLED,
                    error="Task cancelled",
                    error_code="task_cancelled",
                    retries=retries,
                    started=started,
                    routing_decision=routing_decision,
                    preserved_context=preserved_context,
                )
                self._metrics.record_execution(result)
                return result

            try:
                routing_decision = self._router.route_with_fallback(
                    task.capability,
                    task.fallback_capability,
                    policy=RoutingPolicy(capability=task.capability, fallback_capability=task.fallback_capability),
                )
                self._metrics.record_routing(routing_decision)
                agent_id = routing_decision.agent_id
                agent = self._registry.get(agent_id)

                self._metrics.set_active_agents({routing_decision.agent_id})

                agent.validate(task)
                coro = agent.execute(task)
                exec_task = asyncio.create_task(coro)
                self._running_tasks[task.task_id] = exec_task

                try:
                    raw_result = await asyncio.wait_for(exec_task, timeout=timeout)
                except asyncio.CancelledError:
                    last_error = "Task cancelled"
                    result = self._build_result(
                        task,
                        agent_id=agent_id,
                        status=TaskStatus.CANCELLED,
                        error=last_error,
                        error_code="task_cancelled",
                        retries=retries,
                        started=started,
                        routing_decision=routing_decision,
                        preserved_context=preserved_context,
                    )
                    self._metrics.record_execution(result)
                    return result
                finally:
                    self._running_tasks.pop(task.task_id, None)

                if not isinstance(raw_result, TaskResult):
                    raw_result = TaskResult(
                        task_id=task.task_id,
                        agent_id=agent_id,
                        capability=task.capability,
                        status=TaskStatus.COMPLETED,
                        output=dict(raw_result) if isinstance(raw_result, dict) else {"result": raw_result},
                    )

                raw_result.retries = retries
                raw_result.execution_time_ms = round((time.monotonic() - started) * 1000, 2)
                raw_result.routing_decision = {
                    "agent_id": routing_decision.agent_id,
                    "reason": routing_decision.reason,
                    "candidates": list(routing_decision.candidates),
                }
                raw_result.preserved_context = preserved_context
                self._metrics.record_execution(raw_result)
                await self._message_bus.emit_event(
                    agent_id,
                    {"event": "task_completed", "task_id": task.task_id, "capability": task.capability},
                )
                return raw_result

            except asyncio.TimeoutError:
                last_error = f"timeout after {timeout}s"
                if task.task_id in self._running_tasks:
                    self._running_tasks[task.task_id].cancel()
                retries += 1
                if retries > max_retries:
                    result = self._build_result(
                        task,
                        agent_id=agent_id,
                        status=TaskStatus.TIMEOUT,
                        error=last_error,
                        error_code="task_timeout",
                        retries=retries - 1,
                        started=started,
                        routing_decision=routing_decision,
                        preserved_context=preserved_context,
                    )
                    self._metrics.record_execution(result)
                    return result
                await self._backoff(retries)

            except TaskValidationError as exc:
                result = self._build_result(
                    task,
                    agent_id=agent_id or "unknown",
                    status=TaskStatus.FAILED,
                    error=str(exc),
                    error_code=exc.code,
                    retries=retries,
                    started=started,
                    routing_decision=routing_decision,
                    preserved_context=preserved_context,
                )
                self._metrics.record_execution(result)
                return result

            except OrchestratorError as exc:
                last_error = str(exc)
                if exc.code in ("capability_not_routable", "agent_not_found"):
                    result = self._build_result(
                        task,
                        agent_id=agent_id or "unknown",
                        status=TaskStatus.FAILED,
                        error=last_error,
                        error_code=exc.code,
                        retries=retries,
                        started=started,
                        routing_decision=routing_decision,
                        preserved_context=preserved_context,
                    )
                    self._metrics.record_execution(result)
                    return result
                retries += 1
                logger.warning("orchestrator_retry task=%s attempt=%s error=%s", task.task_id, retries, last_error)
                if retries > max_retries:
                    break
                await self._backoff(retries)

            except Exception as exc:
                last_error = str(exc)
                retries += 1
                logger.exception("agent_execution_failed task=%s agent=%s", task.task_id, agent_id)
                if retries > max_retries:
                    break
                await self._backoff(retries)

        result = self._build_result(
            task,
            agent_id=agent_id or "unknown",
            status=TaskStatus.FAILED,
            error=last_error,
            error_code="task_retry_exhausted",
            retries=max(0, retries - 1),
            started=started,
            routing_decision=routing_decision,
            preserved_context=preserved_context,
        )
        self._metrics.record_execution(result)
        await self._message_bus.emit_event(
            agent_id or "orchestrator",
            {"event": "task_failed", "task_id": task.task_id, "error": last_error},
        )
        return result

    async def enqueue(self, task: TaskRequest) -> str:
        await self._queue.put(task)
        self._metrics.set_queue_length(self._queue.qsize())
        return task.task_id

    async def process_queue(self) -> list[TaskResult]:
        results: list[TaskResult] = []
        while not self._queue.empty():
            task = await self._queue.get()
            results.append(await self.execute_async(task))
        self._metrics.set_queue_length(self._queue.qsize())
        return results

    def cancel(self, task_id: str) -> bool:
        self._cancel_flags.add(task_id)
        running = self._running_tasks.get(task_id)
        if running and not running.done():
            running.cancel()
            return True
        return task_id in self._cancel_flags

    async def send_agent_message(self, message: AgentMessage) -> None:
        await self._message_bus.publish(message)

    async def request_agent(
        self,
        source_agent_id: str,
        target_agent_id: str,
        payload: dict[str, Any],
        *,
        timeout_seconds: float = 10.0,
    ) -> AgentMessage:
        return await self._message_bus.request(
            source_agent_id,
            target_agent_id,
            payload,
            timeout_seconds=timeout_seconds,
        )

    def health(self) -> dict[str, Any]:
        return {
            "initialized": self._initialized,
            "agents": self._registry.summary(),
            "metrics": self._metrics.summary(),
            "queue_length": self._queue.qsize(),
        }

    async def _backoff(self, attempt: int) -> None:
        delay = min(
            self._config.retry_base_delay_seconds * (2 ** (attempt - 1)),
            self._config.retry_max_delay_seconds,
        )
        await asyncio.sleep(delay)

    def _build_result(
        self,
        task: TaskRequest,
        *,
        agent_id: str,
        status: TaskStatus,
        error: str | None,
        error_code: str | None,
        retries: int,
        started: float,
        routing_decision: RoutingDecision | None,
        preserved_context: dict[str, Any],
    ) -> TaskResult:
        return TaskResult(
            task_id=task.task_id,
            agent_id=agent_id,
            capability=task.capability,
            status=status,
            output={},
            error=error,
            error_code=error_code,
            retries=retries,
            execution_time_ms=round((time.monotonic() - started) * 1000, 2),
            routing_decision={
                "agent_id": routing_decision.agent_id,
                "reason": routing_decision.reason,
                "candidates": list(routing_decision.candidates),
            }
            if routing_decision
            else {},
            preserved_context=preserved_context,
        )


platform_orchestrator = PlatformOrchestrator()
