# ToolExecutor — sandboxed async tool execution with retry and cancellation.

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

from events.publisher import publish
from platform_tools.audit import ToolAuditLog, tool_audit_log
from platform_tools.config import DEFAULT_TOOL_CONFIG, ToolExecutorConfig
from platform_tools.exceptions import ToolCancelledError, ToolExecutionError, ToolTimeoutError
from platform_tools.metrics import ToolMetrics, tool_metrics
from platform_tools.models import ExecutionProgress, ToolContext, ToolResult
from platform_tools.permissions import ToolPermissionService, tool_permission_service
from platform_tools.registry import ToolRegistry, tool_registry
from platform_tools.tool_events import ToolCompletedEvent, ToolFailedEvent, ToolStartedEvent

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Execute tools with sandboxing, permissions, retry, and audit logging."""

    def __init__(
        self,
        *,
        registry: ToolRegistry | None = None,
        permissions: ToolPermissionService | None = None,
        metrics: ToolMetrics | None = None,
        audit: ToolAuditLog | None = None,
        config: ToolExecutorConfig | None = None,
    ) -> None:
        self._registry = registry or tool_registry
        self._permissions = permissions or tool_permission_service
        self._metrics = metrics or tool_metrics
        self._audit = audit or tool_audit_log
        self._config = config or DEFAULT_TOOL_CONFIG
        self._running: dict[str, asyncio.Task[ToolResult]] = {}
        self._cancel_flags: set[str] = set()
        self._progress: dict[str, ExecutionProgress] = {}
        self._semaphore = asyncio.Semaphore(self._config.max_concurrent_executions)

    def reset(self) -> None:
        for task in self._running.values():
            if not task.done():
                task.cancel()
        self._running.clear()
        self._cancel_flags.clear()
        self._progress.clear()
        self._metrics.reset()
        self._audit.reset()
        self._semaphore = asyncio.Semaphore(self._config.max_concurrent_executions)

    async def execute(
        self,
        tool_id: str,
        payload: dict[str, Any] | None = None,
        *,
        context: ToolContext | None = None,
    ) -> ToolResult:
        return await self._execute_inner(tool_id, payload or {}, context or ToolContext())

    async def execute_concurrent(
        self,
        calls: list[tuple[str, dict[str, Any] | None]],
        *,
        context: ToolContext | None = None,
    ) -> list[ToolResult]:
        ctx = context or ToolContext()
        tasks = [self.execute(tool_id, payload, context=ctx) for tool_id, payload in calls]
        return list(await asyncio.gather(*tasks, return_exceptions=False))

    def cancel(self, execution_id: str) -> bool:
        self._cancel_flags.add(execution_id)
        task = self._running.get(execution_id)
        if task and not task.done():
            task.cancel()
            return True
        return execution_id in self._cancel_flags

    def get_progress(self, execution_id: str) -> ExecutionProgress | None:
        return self._progress.get(execution_id)

    async def _execute_inner(
        self,
        tool_id: str,
        payload: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        tool = self._registry.get(tool_id)
        if not tool.enabled:
            raise ToolExecutionError(tool_id, "Tool is disabled")

        self._permissions.check(tool, context)
        execution_id = str(uuid.uuid4())
        timeout = tool.timeout_seconds or self._config.default_timeout_seconds
        retries = 0
        last_error = ""
        started = time.monotonic()

        await publish(
            ToolStartedEvent(
                tool_id=tool_id,
                execution_id=execution_id,
                agent_id=context.agent_id,
                user_id=context.user_id,
            )
        )

        self._progress[execution_id] = ExecutionProgress(
            execution_id=execution_id, tool_id=tool_id, progress=0.0, message="starting"
        )

        while retries <= self._config.max_retries:
            if execution_id in self._cancel_flags:
                self._cancel_flags.discard(execution_id)
                result = self._failed_result(
                    tool_id, execution_id, "cancelled", started, retries, ToolCancelledError(tool_id)
                )
                self._finalize(result, context, cancelled=True)
                return result

            try:
                async with self._semaphore:
                    assert tool.handler is not None
                    exec_task = asyncio.create_task(tool.handler(context, payload))
                    self._running[execution_id] = exec_task
                    self._progress[execution_id] = ExecutionProgress(
                        execution_id=execution_id, tool_id=tool_id, progress=0.5, message="running"
                    )
                    try:
                        output = await asyncio.wait_for(exec_task, timeout=timeout)
                    except asyncio.CancelledError:
                        result = self._failed_result(tool_id, execution_id, "cancelled", started, retries)
                        self._finalize(result, context, cancelled=True)
                        return result
                    finally:
                        self._running.pop(execution_id, None)

                if not isinstance(output, dict):
                    output = {"result": output}

                result = ToolResult(
                    tool_id=tool_id,
                    success=True,
                    output=output,
                    execution_id=execution_id,
                    execution_time_ms=round((time.monotonic() - started) * 1000, 2),
                    retries=retries,
                    progress=1.0,
                )
                self._progress[execution_id] = ExecutionProgress(
                    execution_id=execution_id, tool_id=tool_id, progress=1.0, message="completed"
                )
                self._finalize(result, context)
                await publish(
                    ToolCompletedEvent(
                        tool_id=tool_id,
                        execution_id=execution_id,
                        execution_time_ms=result.execution_time_ms,
                        agent_id=context.agent_id,
                    )
                )
                return result

            except asyncio.TimeoutError:
                last_error = f"timeout after {timeout}s"
                retries += 1
                if retries > self._config.max_retries:
                    result = self._failed_result(tool_id, execution_id, last_error, started, retries - 1)
                    self._finalize(result, context, error=ToolTimeoutError(tool_id, timeout))
                    return result
                await self._backoff(retries)

            except Exception as exc:
                last_error = str(exc)
                retries += 1
                logger.exception("tool_execution_failed tool=%s attempt=%s", tool_id, retries)
                if retries > self._config.max_retries:
                    break
                await self._backoff(retries)

        result = self._failed_result(tool_id, execution_id, last_error, started, max(0, retries - 1))
        self._finalize(result, context, error=ToolExecutionError(tool_id, last_error))
        await publish(
            ToolFailedEvent(
                tool_id=tool_id,
                execution_id=execution_id,
                error=last_error,
                retries=result.retries,
                agent_id=context.agent_id,
            )
        )
        return result

    def _failed_result(
        self,
        tool_id: str,
        execution_id: str,
        error: str,
        started: float,
        retries: int,
        exc: Exception | None = None,
    ) -> ToolResult:
        return ToolResult(
            tool_id=tool_id,
            success=False,
            error=error,
            execution_id=execution_id,
            execution_time_ms=round((time.monotonic() - started) * 1000, 2),
            retries=retries,
        )

    def _finalize(
        self,
        result: ToolResult,
        context: ToolContext,
        *,
        error: Exception | None = None,
        cancelled: bool = False,
    ) -> None:
        self._metrics.record(result)
        self._audit.record(
            execution_id=result.execution_id,
            tool_id=result.tool_id,
            agent_id=context.agent_id,
            user_id=context.user_id,
            success=result.success,
            error=result.error,
            execution_time_ms=result.execution_time_ms,
            retries=result.retries,
        )
        if not result.success and not cancelled:
            logger.warning("tool_failed id=%s error=%s", result.tool_id, result.error)

    async def _backoff(self, attempt: int) -> None:
        delay = min(
            self._config.retry_base_delay_seconds * (2 ** (attempt - 1)),
            self._config.retry_max_delay_seconds,
        )
        await asyncio.sleep(delay)


tool_executor = ToolExecutor()
