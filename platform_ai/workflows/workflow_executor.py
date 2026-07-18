# Workflow executor — orchestrates steps with retry, fallback, cancel, resume.

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from platform_ai.workflows.exceptions import (
    StepExecutionError,
    WorkflowCancelledError,
    WorkflowExecutionError,
    WorkflowNotFoundError,
)
from platform_ai.workflows.models import (
    ExecutionStatus,
    StepResult,
    StepType,
    WorkflowDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResult,
    WorkflowExecutionState,
    WorkflowStep,
)
from platform_ai.workflows.workflow_context import WorkflowContext
from platform_ai.workflows.workflow_events import (
    AIWorkflowCancelledEvent,
    AIWorkflowCompletedEvent,
    AIWorkflowFailedEvent,
    AIWorkflowStartedEvent,
    StepCompletedEvent,
    StepFailedEvent,
    StepStartedEvent,
    publish_workflow_event,
)
from platform_ai.workflows.workflow_steps import step_runner

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    def __init__(self) -> None:
        self._active: dict[str, WorkflowExecutionState] = {}
        self._cancel_flags: dict[str, bool] = {}

    def reset(self) -> None:
        self._active.clear()
        self._cancel_flags.clear()

    def cancel(self, execution_id: str) -> bool:
        if execution_id not in self._active:
            return False
        self._cancel_flags[execution_id] = True
        state = self._active[execution_id]
        state.cancelled = True
        state.status = ExecutionStatus.CANCELLED
        return True

    def get_state(self, execution_id: str) -> WorkflowExecutionState | None:
        return self._active.get(execution_id)

    def list_active(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._active.values() if s.status == ExecutionStatus.RUNNING]

    async def execute(
        self,
        definition: WorkflowDefinition,
        request: WorkflowExecutionRequest,
        *,
        resume_state: WorkflowExecutionState | None = None,
    ) -> WorkflowExecutionResult:
        execution_id = resume_state.execution_id if resume_state else request.execution_id
        self._cancel_flags[execution_id] = False

        ctx = WorkflowContext(
            workflow_id=definition.workflow_id,
            execution_id=execution_id,
            plugin_id=request.plugin_id,
            user_id=request.user_id,
            input=dict(request.input),
            memory=dict(resume_state.memory) if resume_state else {},
            step_results=dict(resume_state.step_results) if resume_state else {},
            configuration=request.input.get("configuration", {}),
            conversation=request.input.get("conversation", {}),
            files=request.input.get("files", []),
            history=request.input.get("history", []),
        )

        from platform_ai.memory.memory_service import memory_service

        ai_context = await memory_service.build_ai_context(
            query=str(request.input)[:500],
            plugin_id=request.plugin_id,
            user_id=request.user_id,
            workflow_id=definition.workflow_id,
            configuration=ctx.configuration,
        )
        ctx.configuration["memory"] = ai_context.to_dict()

        state = resume_state or WorkflowExecutionState(
            execution_id=execution_id,
            workflow_id=definition.workflow_id,
            status=ExecutionStatus.RUNNING,
            input=dict(request.input),
            plugin_id=request.plugin_id,
            user_id=request.user_id,
        )
        self._active[execution_id] = state
        start = time.perf_counter()
        step_results: list[StepResult] = []
        total_cost = 0.0
        current_step_id = resume_state.current_step if resume_state else definition.entry_step

        await publish_workflow_event(
            AIWorkflowStartedEvent(
                workflow_id=definition.workflow_id,
                execution_id=execution_id,
                plugin_id=request.plugin_id or "",
            )
        )

        def _is_cancelled() -> bool:
            return self._cancel_flags.get(execution_id, False)

        async def _run_single(step: WorkflowStep, *, record: bool = True) -> StepResult:
            await publish_workflow_event(
                StepStartedEvent(
                    workflow_id=definition.workflow_id,
                    execution_id=execution_id,
                    step_id=step.step_id,
                )
            )
            last_error: Exception | None = None
            attempts = step.retries + 1
            for attempt in range(attempts):
                try:
                    if step.step_type == StepType.PARALLEL.value:
                        result = await step_runner.run(
                            step,
                            ctx,
                            plugin_id=request.plugin_id,
                            user_id=request.user_id,
                            use_cache=request.use_cache,
                            is_cancelled=_is_cancelled,
                            parallel_steps=definition.steps,
                            executor_fn=lambda s: _run_single(s, record=True),
                        )
                    else:
                        result = await step_runner.run(
                            step,
                            ctx,
                            plugin_id=request.plugin_id,
                            user_id=request.user_id,
                            use_cache=request.use_cache,
                            is_cancelled=_is_cancelled,
                        )
                    await publish_workflow_event(
                        StepCompletedEvent(
                            workflow_id=definition.workflow_id,
                            execution_id=execution_id,
                            step_id=step.step_id,
                            latency_ms=result.latency_ms,
                        )
                    )
                    if record:
                        step_results.append(result)
                    return result
                except WorkflowCancelledError:
                    raise
                except Exception as exc:
                    last_error = exc
                    if attempt < attempts - 1:
                        logger.warning("step_retry step=%s attempt=%d", step.step_id, attempt + 1)
                        continue
            if last_error:
                await publish_workflow_event(
                    StepFailedEvent(
                        workflow_id=definition.workflow_id,
                        execution_id=execution_id,
                        step_id=step.step_id,
                        error=str(last_error),
                    )
                )
                if step.fallback and step.fallback in definition.steps:
                    fallback_step = definition.steps[step.fallback]
                    return await _run_single(fallback_step)
                raise StepExecutionError(step.step_id, str(last_error)) from last_error
            raise StepExecutionError(step.step_id, "Unknown step failure")

        try:
            visited: set[str] = set()
            while current_step_id:
                if _is_cancelled():
                    raise WorkflowCancelledError("Workflow cancelled")
                if current_step_id in visited and current_step_id not in ("end",):
                    logger.warning("workflow_cycle_detected step=%s", current_step_id)
                    break
                visited.add(current_step_id)

                if current_step_id == "end":
                    break
                if current_step_id not in definition.steps:
                    raise WorkflowExecutionError(f"Step not found: {current_step_id}")

                step = definition.steps[current_step_id]
                state.current_step = current_step_id
                result = await _run_single(step, record=False)
                step_results.append(result)
                total_cost += result.cost_usd
                state.step_results[step.step_id] = result
                state.memory = dict(ctx.memory)

                if result.output.get("_paused"):
                    state.status = ExecutionStatus.PAUSED
                    break

                current_step_id = self._next_step(step, result, definition)

            if state.status == ExecutionStatus.PAUSED:
                status = ExecutionStatus.PAUSED.value
            elif _is_cancelled():
                status = ExecutionStatus.CANCELLED.value
            else:
                status = ExecutionStatus.COMPLETED.value
                state.status = ExecutionStatus.COMPLETED

            latency = (time.perf_counter() - start) * 1000
            output = ctx.memory.get("_output") or ctx.memory.get("final") or dict(ctx.memory)
            exec_result = WorkflowExecutionResult(
                execution_id=execution_id,
                workflow_id=definition.workflow_id,
                status=status,
                output=output if isinstance(output, dict) else {"result": output},
                step_results=step_results,
                memory=dict(ctx.memory),
                latency_ms=latency,
                cost_usd=total_cost,
                current_step=state.current_step,
            )

            state.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            if status == ExecutionStatus.COMPLETED.value:
                await publish_workflow_event(
                    AIWorkflowCompletedEvent(
                        workflow_id=definition.workflow_id,
                        execution_id=execution_id,
                        plugin_id=request.plugin_id or "",
                        latency_ms=latency,
                        cost_usd=total_cost,
                    )
                )
            elif status == ExecutionStatus.CANCELLED.value:
                await publish_workflow_event(
                    AIWorkflowCancelledEvent(
                        workflow_id=definition.workflow_id,
                        execution_id=execution_id,
                        plugin_id=request.plugin_id or "",
                    )
                )
            return exec_result

        except WorkflowCancelledError:
            latency = (time.perf_counter() - start) * 1000
            state.status = ExecutionStatus.CANCELLED
            await publish_workflow_event(
                AIWorkflowCancelledEvent(
                    workflow_id=definition.workflow_id,
                    execution_id=execution_id,
                    plugin_id=request.plugin_id or "",
                )
            )
            return WorkflowExecutionResult(
                execution_id=execution_id,
                workflow_id=definition.workflow_id,
                status=ExecutionStatus.CANCELLED.value,
                step_results=step_results,
                memory=dict(ctx.memory),
                latency_ms=latency,
                cost_usd=total_cost,
                error="cancelled",
            )
        except Exception as exc:
            latency = (time.perf_counter() - start) * 1000
            state.status = ExecutionStatus.FAILED
            state.error = str(exc)
            await publish_workflow_event(
                AIWorkflowFailedEvent(
                    workflow_id=definition.workflow_id,
                    execution_id=execution_id,
                    plugin_id=request.plugin_id or "",
                    error=str(exc),
                )
            )
            return WorkflowExecutionResult(
                execution_id=execution_id,
                workflow_id=definition.workflow_id,
                status=ExecutionStatus.FAILED.value,
                step_results=step_results,
                memory=dict(ctx.memory),
                latency_ms=latency,
                cost_usd=total_cost,
                error=str(exc),
                current_step=state.current_step,
            )
        finally:
            if state.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED):
                self._active.pop(execution_id, None)
                self._cancel_flags.pop(execution_id, None)

    def _next_step(self, step: WorkflowStep, result: StepResult, definition: WorkflowDefinition) -> str | None:
        if result.output.get("_next_override"):
            nxt = result.output["_next_override"]
            return None if nxt in ("end", None) else nxt
        if step.step_type == StepType.CONDITION.value:
            return step.on_true if result.output.get("result") else step.on_false
        if step.step_type == StepType.BRANCH.value:
            nxt = result.output.get("branch")
            return None if nxt in ("end", None) else nxt
        if step.step_type == StepType.PARALLEL.value:
            return step.next
        nxt = step.next
        return None if nxt in ("end", None) else nxt


workflow_executor = WorkflowExecutor()
