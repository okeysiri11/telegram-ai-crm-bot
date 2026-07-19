# WorkflowExecutor — unified step loop with retry, fallback, pause, cancel.

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from platform_workflows.context import WorkflowContext
from platform_workflows.exceptions import (
    StepExecutionError,
    WorkflowCancelledError,
    WorkflowExecutionError,
    WorkflowNotFoundError,
)
from platform_workflows.models import (
    ExecutionStatus,
    StepDefinition,
    StepResult,
    StepType,
    WorkflowDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResult,
)
from platform_workflows.workflow_steps import workflow_steps

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    def __init__(self) -> None:
        self._active: dict[str, WorkflowContext] = {}
        self._cancel_flags: dict[str, bool] = {}

    def reset(self) -> None:
        self._active.clear()
        self._cancel_flags.clear()

    def cancel(self, execution_id: str) -> bool:
        if execution_id not in self._active:
            return False
        self._cancel_flags[execution_id] = True
        ctx = self._active[execution_id]
        ctx.status = ExecutionStatus.CANCELLED
        return True

    def get_context(self, execution_id: str) -> WorkflowContext | None:
        return self._active.get(execution_id)

    def list_active(self) -> list[dict[str, Any]]:
        return [
            c.to_dict()
            for c in self._active.values()
            if c.status in {ExecutionStatus.RUNNING, ExecutionStatus.WAITING, ExecutionStatus.PAUSED}
        ]

    async def execute_step(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        definition: WorkflowDefinition,
        *,
        user_input: Any | None = None,
        callback_data: str | None = None,
        request: WorkflowExecutionRequest | None = None,
    ) -> tuple[WorkflowContext, StepResult, str | None, bool]:
        is_cancelled = lambda: self._cancel_flags.get(context.execution_id, False)

        async def _run_single(target: StepDefinition) -> tuple[WorkflowContext, StepResult]:
            last_error: Exception | None = None
            attempts = target.retries + 1
            for attempt in range(attempts):
                try:
                    ctx, result, _, _ = await workflow_steps.execute(
                        target,
                        context,
                        user_input=user_input,
                        callback_data=callback_data,
                        plugin_id=request.plugin_id if request else context.plugin_id,
                        user_id=request.user_id if request else context.user_id,
                        use_cache=request.use_cache if request else True,
                        is_cancelled=is_cancelled,
                        all_steps=definition.steps,
                        executor_fn=_run_single,
                    )
                    context.current_step = target.id
                    context.touch()
                    return ctx, result
                except WorkflowCancelledError:
                    raise
                except Exception as exc:
                    last_error = exc
                    if attempt < attempts - 1:
                        logger.warning("step_retry step=%s attempt=%d", target.id, attempt + 1)
                        continue
            if last_error and target.fallback and target.fallback in definition.steps:
                return await _run_single(definition.steps[target.fallback])
            raise StepExecutionError(target.id, str(last_error) if last_error else "step failed")

        _, result, next_id, pause = await workflow_steps.execute(
            step,
            context,
            user_input=user_input,
            callback_data=callback_data,
            plugin_id=request.plugin_id if request else context.plugin_id,
            user_id=request.user_id if request else context.user_id,
            use_cache=request.use_cache if request else True,
            is_cancelled=is_cancelled,
            all_steps=definition.steps,
            executor_fn=_run_single,
        )
        context.current_step = step.id
        context.touch()
        next_step = self._resolve_next(step, result, next_id)
        return context, result, next_step, pause

    async def run(
        self,
        definition: WorkflowDefinition,
        context: WorkflowContext,
        *,
        request: WorkflowExecutionRequest | None = None,
        user_input: Any | None = None,
        callback_data: str | None = None,
        resume: bool = False,
    ) -> WorkflowExecutionResult:
        execution_id = context.execution_id
        self._cancel_flags[execution_id] = False
        self._active[execution_id] = context
        context.status = ExecutionStatus.RUNNING
        start = time.perf_counter()
        step_results: list[StepResult] = []
        total_cost = 0.0

        step_id = context.current_step or definition.entry_step or (definition.first_step().id if definition.first_step() else None)
        if not step_id:
            raise WorkflowExecutionError("Workflow has no entry step")

        step_user_input = user_input
        step_callback_data = callback_data

        try:
            visited: set[str] = set()
            while step_id and step_id != "end":
                if self._cancel_flags.get(execution_id):
                    raise WorkflowCancelledError("Workflow cancelled")
                if step_id in visited:
                    logger.warning("workflow_cycle_detected step=%s", step_id)
                    break
                visited.add(step_id)

                step = definition.step_by_id(step_id)
                if step is None:
                    raise WorkflowExecutionError(f"Step not found: {step_id}")

                _, result, next_id, pause = await self.execute_step(
                    step,
                    context,
                    definition,
                    user_input=step_user_input,
                    callback_data=step_callback_data,
                    request=request,
                )
                step_results.append(result)
                if step.type == StepType.PARALLEL:
                    for branch_payload in (result.output.get("results") or {}).values():
                        if isinstance(branch_payload, dict) and "step_id" in branch_payload:
                            step_results.append(
                                StepResult(
                                    step_id=str(branch_payload["step_id"]),
                                    step_type=str(branch_payload.get("step_type", "skill")),
                                    success=bool(branch_payload.get("success", True)),
                                    output=dict(branch_payload.get("output") or {}),
                                    latency_ms=float(branch_payload.get("latency_ms") or 0),
                                    cost_usd=float(branch_payload.get("cost_usd") or 0),
                                )
                            )
                total_cost += result.cost_usd
                resume = False
                step_user_input = None
                step_callback_data = None

                if pause or context.status in {ExecutionStatus.WAITING, ExecutionStatus.PAUSED}:
                    break
                if context.status == ExecutionStatus.COMPLETED:
                    break
                step_id = next_id

            if context.status == ExecutionStatus.COMPLETED:
                status = ExecutionStatus.COMPLETED.value.lower()
            elif context.status == ExecutionStatus.PAUSED:
                status = ExecutionStatus.PAUSED.value.lower()
            elif context.status == ExecutionStatus.WAITING:
                status = ExecutionStatus.WAITING.value.lower()
            elif self._cancel_flags.get(execution_id):
                status = ExecutionStatus.CANCELLED.value.lower()
                context.status = ExecutionStatus.CANCELLED
            else:
                context.status = ExecutionStatus.COMPLETED
                status = ExecutionStatus.COMPLETED.value.lower()

            latency = (time.perf_counter() - start) * 1000
            output = context.memory.get("_output") or context.memory.get("final") or dict(context.memory)
            return WorkflowExecutionResult(
                execution_id=execution_id,
                workflow_id=definition.id,
                status=status,
                output=output if isinstance(output, dict) else {"result": output},
                step_results=step_results,
                memory=dict(context.memory),
                latency_ms=latency,
                cost_usd=total_cost,
                current_step=context.current_step,
                context=context.to_dict(),
            )
        except WorkflowCancelledError:
            latency = (time.perf_counter() - start) * 1000
            context.status = ExecutionStatus.CANCELLED
            return WorkflowExecutionResult(
                execution_id=execution_id,
                workflow_id=definition.id,
                status=ExecutionStatus.CANCELLED.value.lower(),
                step_results=step_results,
                memory=dict(context.memory),
                latency_ms=latency,
                cost_usd=total_cost,
                error="cancelled",
                context=context.to_dict(),
            )
        except Exception as exc:
            latency = (time.perf_counter() - start) * 1000
            context.status = ExecutionStatus.FAILED
            context.error = str(exc)
            return WorkflowExecutionResult(
                execution_id=execution_id,
                workflow_id=definition.id,
                status=ExecutionStatus.FAILED.value.lower(),
                step_results=step_results,
                memory=dict(context.memory),
                latency_ms=latency,
                cost_usd=total_cost,
                error=str(exc),
                current_step=context.current_step,
                context=context.to_dict(),
            )
        finally:
            if context.status in {
                ExecutionStatus.COMPLETED,
                ExecutionStatus.FAILED,
                ExecutionStatus.CANCELLED,
            }:
                self._active.pop(execution_id, None)
                self._cancel_flags.pop(execution_id, None)

    def _resolve_next(
        self,
        step: StepDefinition,
        result: StepResult,
        explicit_next: str | None,
    ) -> str | None:
        if result.output.get("_next_override"):
            nxt = result.output["_next_override"]
            return None if nxt in ("end", None) else str(nxt)
        if step.type == StepType.CONDITION:
            branch = step.on_true if result.output.get("result") else step.on_false
            nxt = branch or explicit_next or step.next_step
            return None if nxt in ("end", None) else str(nxt)
        if step.type == StepType.BRANCH:
            nxt = result.output.get("branch") or explicit_next or step.next_step
            return None if nxt in ("end", None) else str(nxt)
        nxt = explicit_next or step.next_step
        return None if nxt in ("end", None) else str(nxt)

    @staticmethod
    async def run_legacy_step(
        step: StepDefinition,
        context: WorkflowContext,
        *,
        user_input: Any | None = None,
        callback_data: str | None = None,
    ) -> tuple[WorkflowContext, str | None, bool]:
        """Backward-compatible step execution API."""
        ctx, _result, next_id, pause = await workflow_steps.execute(
            step,
            context,
            user_input=user_input,
            callback_data=callback_data,
        )
        return ctx, next_id, pause


# Backward-compatible alias used by legacy tests and facades.
execute_step = WorkflowExecutor.run_legacy_step

workflow_executor = WorkflowExecutor()
