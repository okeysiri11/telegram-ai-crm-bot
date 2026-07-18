# WorkflowEngine — orchestrates configurable vertical workflows.

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from events.event_bus import publish
from events.workflow_events import (
    WorkflowCancelledEvent,
    WorkflowCompletedEvent,
    WorkflowStartedEvent,
    WorkflowStepCompletedEvent,
)
from workflow.models import ExecutionStatus, WorkflowDefinition
from workflow.workflow_context import WorkflowContext
from workflow.workflow_executor import WorkflowExecutor
from workflow.workflow_registry import WorkflowRegistry, workflow_registry

logger = logging.getLogger(__name__)

_step_durations_ms: list[float] = []
_execution_durations_ms: list[float] = []
_success_count = 0
_failure_count = 0
_MAX_SAMPLES = 500


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowEngine:
    def __init__(self, registry: WorkflowRegistry | None = None) -> None:
        self.registry = registry or workflow_registry
        self._active: dict[str, WorkflowContext] = {}

    async def run_backend_workflow(
        self,
        vertical: str,
        *,
        telegram_user: dict[str, Any] | None = None,
        request: dict[str, Any] | None = None,
        manager: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
    ) -> WorkflowContext | None:
        """Run a vertical backend workflow (service/event steps only) after request creation."""
        definition = self.registry.get_for_vertical(vertical)
        if definition is None:
            return None

        first = definition.first_step()
        if first is None:
            return None

        context = WorkflowContext.create(
            workflow_id=definition.id,
            vertical=definition.vertical,
            telegram_user=telegram_user,
            variables=variables,
            current_step=first.id,
        )
        context.request = dict(request or {})
        context.manager = dict(manager or {})
        context.status = ExecutionStatus.RUNNING
        self._active[context.execution_id] = context

        await self._persist(context)
        await publish(
            WorkflowStartedEvent(
                execution_id=context.execution_id,
                workflow_id=definition.id,
                vertical=context.vertical,
                telegram_user_id=context.telegram_user.get("id"),
                current_step=first.id,
            )
        )
        return await self._continue_from(context, definition, first.id)

    async def start(
        self,
        workflow_id: str,
        *,
        telegram_user: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        vertical: str | None = None,
    ) -> WorkflowContext:
        definition = self._resolve_definition(workflow_id, vertical)
        first = definition.first_step()
        if first is None:
            raise ValueError(f"Workflow {workflow_id} has no steps")

        context = WorkflowContext.create(
            workflow_id=definition.id,
            vertical=vertical or definition.vertical,
            telegram_user=telegram_user,
            variables=variables,
            metadata=metadata,
            current_step=first.id,
        )
        context.status = ExecutionStatus.RUNNING
        self._active[context.execution_id] = context

        await self._persist(context)
        await publish(
            WorkflowStartedEvent(
                execution_id=context.execution_id,
                workflow_id=definition.id,
                vertical=context.vertical,
                telegram_user_id=context.telegram_user.get("id"),
                current_step=first.id,
            )
        )

        return await self.run_until_waiting(context.execution_id)

    async def start_for_vertical(
        self,
        vertical: str,
        **kwargs: Any,
    ) -> WorkflowContext:
        definition = self.registry.get_for_vertical(vertical)
        if definition is None:
            raise ValueError(f"No workflow registered for vertical {vertical}")
        return await self.start(definition.id, vertical=vertical, **kwargs)

    async def advance(
        self,
        execution_id: str,
        *,
        user_input: Any | None = None,
        callback_data: str | None = None,
    ) -> WorkflowContext:
        context = await self._load(execution_id)
        if context.status in {ExecutionStatus.COMPLETED, ExecutionStatus.CANCELLED, ExecutionStatus.FAILED}:
            return context

        definition = self._resolve_definition(context.workflow_id, context.vertical)
        step = definition.step_by_id(context.current_step or "")
        if step is None:
            context.status = ExecutionStatus.FAILED
            context.error = f"Unknown step {context.current_step}"
            await self._finalize(context, success=False)
            return context

        context.status = ExecutionStatus.RUNNING
        next_id = step.next_step

        if step.is_interactive or step.type.value == "choice":
            _, next_id, _ = await WorkflowExecutor.execute_step(
                step,
                context,
                user_input=user_input,
                callback_data=callback_data,
            )
        else:
            context, next_id, _ = await WorkflowExecutor.execute_step(
                step,
                context,
                user_input=user_input,
                callback_data=callback_data,
            )

        if context.status == ExecutionStatus.WAITING:
            await self._persist(context)
            return context

        return await self._continue_from(context, definition, next_id)

    async def run_until_waiting(self, execution_id: str) -> WorkflowContext:
        context = await self._load(execution_id)
        definition = self._resolve_definition(context.workflow_id, context.vertical)
        step_id = context.current_step
        return await self._continue_from(context, definition, step_id)

    async def _continue_from(
        self,
        context: WorkflowContext,
        definition: WorkflowDefinition,
        step_id: str | None,
    ) -> WorkflowContext:
        visited = 0
        while step_id and visited < 100:
            visited += 1
            step = definition.step_by_id(step_id)
            if step is None:
                context.status = ExecutionStatus.FAILED
                context.error = f"Unknown step {step_id}"
                break

            started = time.monotonic()
            context, next_id, pause = await WorkflowExecutor.execute_step(step, context)
            duration_ms = (time.monotonic() - started) * 1000.0
            _step_durations_ms.append(duration_ms)
            if len(_step_durations_ms) > _MAX_SAMPLES:
                del _step_durations_ms[0]

            await publish(
                WorkflowStepCompletedEvent(
                    execution_id=context.execution_id,
                    workflow_id=context.workflow_id,
                    step_id=step.id,
                    step_type=step.type.value,
                    duration_ms=round(duration_ms, 2),
                    status=context.status.value,
                )
            )
            await self._log_step(context, step.id, step.type.value, duration_ms)

            if pause or context.status == ExecutionStatus.WAITING:
                self._active[context.execution_id] = context
                await self._persist(context)
                return context

            if context.status == ExecutionStatus.COMPLETED:
                await self._finalize(context, success=True)
                return context

            step_id = next_id

        if context.status not in {ExecutionStatus.COMPLETED, ExecutionStatus.CANCELLED}:
            if not context.error:
                context.status = ExecutionStatus.COMPLETED
                context.completed_at = _utcnow()
            await self._finalize(context, success=context.status == ExecutionStatus.COMPLETED)

        return context

    async def cancel(self, execution_id: str, *, reason: str = "user_cancelled") -> WorkflowContext:
        context = await self._load(execution_id)
        context.status = ExecutionStatus.CANCELLED
        context.error = reason
        context.completed_at = _utcnow()
        context.touch()
        await self._persist(context)
        self._active.pop(execution_id, None)

        await publish(
            WorkflowCancelledEvent(
                execution_id=context.execution_id,
                workflow_id=context.workflow_id,
                vertical=context.vertical,
                reason=reason,
                current_step=context.current_step,
            )
        )
        return context

    async def get_statistics(self) -> dict[str, Any]:
        from repositories.workflow_execution_repository import WorkflowExecutionRepository
        from database.session import get_session

        async with get_session() as session:
            db_stats = await WorkflowExecutionRepository(session).get_statistics()

        total = _success_count + _failure_count
        avg_exec = (
            round(sum(_execution_durations_ms) / len(_execution_durations_ms), 2)
            if _execution_durations_ms
            else db_stats.get("average_execution_time_ms", 0.0)
        )
        avg_step = (
            round(sum(_step_durations_ms) / len(_step_durations_ms), 2)
            if _step_durations_ms
            else 0.0
        )

        return {
            "registered_workflows": [w.to_dict() for w in self.registry.list_all()],
            "active_executions": len(self._active),
            "completed_today": db_stats.get("completed_today", 0),
            "failed_today": db_stats.get("failed_today", 0),
            "average_execution_time_ms": avg_exec,
            "kpi": {
                "workflow_execution_time_ms": avg_exec,
                "workflow_success_rate": round(_success_count / max(total, 1), 4),
                "workflow_failure_rate": round(_failure_count / max(total, 1), 4),
                "step_execution_time_ms": avg_step,
                "active_workflows": len(self._active),
            },
            **db_stats,
        }

    def load_definitions(self) -> int:
        return self.registry.load_from_directory()

    def _resolve_definition(self, workflow_id: str, vertical: str | None) -> WorkflowDefinition:
        definition = self.registry.get(workflow_id)
        if definition is None and vertical:
            definition = self.registry.get_for_vertical(vertical)
        if definition is None:
            raise ValueError(f"Workflow not found: {workflow_id}")
        return definition

    async def _finalize(self, context: WorkflowContext, *, success: bool) -> None:
        global _success_count, _failure_count
        if success:
            _success_count += 1
            context.status = ExecutionStatus.COMPLETED
        else:
            _failure_count += 1
            if context.status != ExecutionStatus.CANCELLED:
                context.status = ExecutionStatus.FAILED

        context.completed_at = context.completed_at or _utcnow()
        duration_ms = (context.completed_at - context.started_at).total_seconds() * 1000.0
        _execution_durations_ms.append(duration_ms)
        if len(_execution_durations_ms) > _MAX_SAMPLES:
            del _execution_durations_ms[0]

        await self._persist(context)
        self._active.pop(context.execution_id, None)

        if success:
            await publish(
                WorkflowCompletedEvent(
                    execution_id=context.execution_id,
                    workflow_id=context.workflow_id,
                    vertical=context.vertical,
                    duration_ms=round(duration_ms, 2),
                    request_number=context.request.get("request_number"),
                )
            )
        else:
            await publish(
                WorkflowCancelledEvent(
                    execution_id=context.execution_id,
                    workflow_id=context.workflow_id,
                    vertical=context.vertical,
                    reason=context.error or "failed",
                    current_step=context.current_step,
                )
            )

    async def _persist(self, context: WorkflowContext) -> None:
        from repositories.workflow_execution_repository import WorkflowExecutionRepository
        from database.session import get_session

        try:
            async with get_session() as session:
                await WorkflowExecutionRepository(session).upsert(context)
        except Exception:
            logger.warning("workflow_persist_failed execution=%s", context.execution_id, exc_info=True)
            self._active[context.execution_id] = context

    async def _load(self, execution_id: str) -> WorkflowContext:
        if execution_id in self._active:
            return self._active[execution_id]

        from repositories.workflow_execution_repository import WorkflowExecutionRepository
        from database.session import get_session

        async with get_session() as session:
            row = await WorkflowExecutionRepository(session).get_by_id(execution_id)
        if row is None:
            raise ValueError(f"Workflow execution not found: {execution_id}")
        context = WorkflowContext.from_dict(row)
        self._active[execution_id] = context
        return context

    async def _log_step(
        self,
        context: WorkflowContext,
        step_id: str,
        step_type: str,
        duration_ms: float,
    ) -> None:
        from repositories.workflow_execution_repository import WorkflowExecutionRepository
        from database.session import get_session

        try:
            async with get_session() as session:
                await WorkflowExecutionRepository(session).log_step(
                    execution_id=context.execution_id,
                    step_id=step_id,
                    step_type=step_type,
                    duration_ms=duration_ms,
                    status=context.status.value,
                )
        except Exception:
            logger.debug("workflow_step_log_skipped execution=%s", context.execution_id, exc_info=True)


workflow_engine = WorkflowEngine()
