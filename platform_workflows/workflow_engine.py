# WorkflowEngine — single orchestration entry point for all business flows.

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
from platform_workflows.context import WorkflowContext
from platform_workflows.exceptions import WorkflowNotFoundError, WorkflowValidationError
from platform_workflows.models import (
    ExecutionStatus,
    WorkflowDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResult,
)
from platform_workflows.workflow_executor import workflow_executor
from platform_workflows.workflow_loader import WorkflowLoader, parse_workflow_document
from platform_workflows.workflow_registry import WorkflowRegistry, workflow_registry
from platform_workflows.workflow_validator import WorkflowValidator

logger = logging.getLogger(__name__)

_step_durations_ms: list[float] = []
_execution_durations_ms: list[float] = []
_success_count = 0
_failure_count = 0
_MAX_SAMPLES = 500
_ai_cache: dict[str, WorkflowExecutionResult] = {}
_ai_history: list[dict[str, Any]] = []


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowEngine:
    """Unified workflow engine — YAML, Python, AI, interactive, and backend flows."""

    def __init__(self, registry: WorkflowRegistry | None = None) -> None:
        self.registry = registry or workflow_registry
        self._initialized = False

    @property
    def _active(self) -> dict[str, WorkflowContext]:
        """Backward-compatible access to in-memory executions."""
        return workflow_executor._active  # type: ignore[return-value]

    def reset(self) -> None:
        self.registry.clear()
        workflow_executor.reset()
        _ai_history.clear()
        _ai_cache.clear()
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        self.registry.load_from_directory()
        from platform_workflows.adapters.python_definitions import register_builtin_workflows

        register_builtin_workflows(self.registry)
        try:
            from platform_ai.skills.skill_manager import skill_manager

            skill_manager.initialize()
        except Exception:
            logger.debug("skill_manager_init_skipped", exc_info=True)
        self._initialized = True
        logger.info("workflow_engine_initialized workflows=%d", len(self.registry.list_ids()))

    def register(self, definition: WorkflowDefinition) -> None:
        WorkflowValidator.validate_or_raise(definition)
        self.registry.register(definition)

    def register_from_dict(self, data: dict[str, Any]) -> WorkflowDefinition:
        definition = parse_workflow_document(data)
        self.register(definition)
        return definition

    def load_definitions(self) -> int:
        self.initialize()
        return len(self.registry.list_ids())

    async def execute(self, request: WorkflowExecutionRequest) -> WorkflowExecutionResult:
        self.initialize()
        definition = self.registry.get(request.workflow_id)
        if definition is None:
            raise WorkflowNotFoundError(f"Workflow not found: {request.workflow_id}")
        if not definition.enabled:
            raise WorkflowValidationError(f"Workflow disabled: {request.workflow_id}")

        cache_key = f"{request.workflow_id}:{hash(str(sorted(request.input.items())))}"
        if request.use_cache and cache_key in _ai_cache:
            cached = _ai_cache[cache_key]
            cached.cached = True
            return cached

        context = WorkflowContext.create(
            workflow_id=definition.id,
            vertical=request.vertical or definition.vertical,
            telegram_user=request.telegram_user,
            variables=request.variables,
            input=request.input,
            plugin_id=request.plugin_id,
            user_id=request.user_id,
            current_step=definition.entry_step,
        )
        if request.request:
            context.request = dict(request.request)
        if request.manager:
            context.manager = dict(request.manager)
        if request.execution_id:
            context.execution_id = request.execution_id

        await publish(
            WorkflowStartedEvent(
                execution_id=context.execution_id,
                workflow_id=definition.id,
                vertical=context.vertical,
                telegram_user_id=context.telegram_user.get("id"),
                current_step=context.current_step,
            )
        )

        result = await workflow_executor.run(definition, context, request=request)
        await self._record_execution(context, result)
        _ai_history.append(
            {
                "execution_id": result.execution_id,
                "workflow_id": result.workflow_id,
                "status": result.status,
                "latency_ms": result.latency_ms,
                "cost_usd": result.cost_usd,
                "timestamp": _utcnow().isoformat(),
            }
        )
        if len(_ai_history) > 500:
            del _ai_history[: len(_ai_history) - 500]

        if request.use_cache and result.status == ExecutionStatus.COMPLETED.value:
            _ai_cache[cache_key] = result

        return result

    async def run_backend_workflow(
        self,
        vertical: str,
        *,
        telegram_user: dict[str, Any] | None = None,
        request: dict[str, Any] | None = None,
        manager: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
    ) -> WorkflowContext | None:
        self.initialize()
        definition = self.registry.get_for_vertical(vertical)
        if definition is None:
            return None
        exec_request = WorkflowExecutionRequest(
            workflow_id=definition.id,
            vertical=vertical,
            telegram_user=telegram_user,
            request=request,
            manager=manager,
            variables=variables,
            use_cache=False,
        )
        result = await self.execute(exec_request)
        if result.context:
            return WorkflowContext.from_dict(result.context)
        return None

    async def start(
        self,
        workflow_id: str,
        *,
        telegram_user: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        vertical: str | None = None,
    ) -> WorkflowContext:
        exec_request = WorkflowExecutionRequest(
            workflow_id=workflow_id,
            vertical=vertical or "",
            telegram_user=telegram_user,
            variables=variables,
            use_cache=False,
        )
        result = await self.execute(exec_request)
        if result.context:
            ctx = WorkflowContext.from_dict(result.context)
            ctx.metadata = dict(metadata or {})
            return ctx
        raise WorkflowNotFoundError(f"Failed to start workflow: {workflow_id}")

    async def start_for_vertical(self, vertical: str, **kwargs: Any) -> WorkflowContext:
        self.initialize()
        definition = self.registry.get_for_vertical(vertical)
        if definition is None:
            raise WorkflowNotFoundError(f"No workflow registered for vertical {vertical}")
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
        exec_request = WorkflowExecutionRequest(
            workflow_id=definition.id,
            execution_id=execution_id,
            vertical=context.vertical,
            variables=context.variables,
            use_cache=False,
        )
        result = await workflow_executor.run(
            definition,
            context,
            request=exec_request,
            user_input=user_input,
            callback_data=callback_data,
            resume=True,
        )
        await self._record_execution(context, result)
        return WorkflowContext.from_dict(result.context or context.to_dict())

    async def run_until_waiting(self, execution_id: str) -> WorkflowContext:
        return await self.advance(execution_id)

    async def _continue_from(
        self,
        context: WorkflowContext,
        definition: WorkflowDefinition,
        step_id: str | None,
    ) -> WorkflowContext:
        context.current_step = step_id
        workflow_executor._active[context.execution_id] = context
        result = await workflow_executor.run(
            definition,
            context,
            request=WorkflowExecutionRequest(
                workflow_id=definition.id,
                execution_id=context.execution_id,
                vertical=context.vertical,
                variables=context.variables,
                use_cache=False,
            ),
            resume=True,
        )
        await self._record_execution(context, result)
        if result.context:
            return WorkflowContext.from_dict(result.context)
        return context

    async def resume(self, execution_id: str) -> WorkflowExecutionResult:
        context = await self._load(execution_id)
        if context.status != ExecutionStatus.PAUSED:
            raise WorkflowNotFoundError(f"No paused execution: {execution_id}")
        definition = self._resolve_definition(context.workflow_id, context.vertical)
        context.status = ExecutionStatus.RUNNING
        result = await workflow_executor.run(
            definition,
            context,
            request=WorkflowExecutionRequest(
                workflow_id=definition.id,
                execution_id=execution_id,
                vertical=context.vertical,
                input=context.input,
                use_cache=False,
            ),
            resume=True,
        )
        await self._record_execution(context, result)
        return result

    async def cancel(self, execution_id: str, *, reason: str = "user_cancelled") -> WorkflowContext:
        context = await self._load(execution_id)
        workflow_executor.cancel(execution_id)
        context.status = ExecutionStatus.CANCELLED
        context.error = reason
        context.completed_at = _utcnow()
        context.touch()
        await self._persist(context)
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

    def list_workflows(self) -> list[dict[str, Any]]:
        self.initialize()
        return [w.to_dict() for w in self.registry.list_all()]

    def list_templates(self) -> list[dict[str, Any]]:
        from platform_workflows.adapters.python_definitions import list_template_metadata

        return list_template_metadata()

    def history(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(reversed(_ai_history[-limit:]))

    def active(self) -> list[dict[str, Any]]:
        return workflow_executor.list_active()

    def metrics(self, workflow_id: str | None = None) -> dict[str, Any]:
        stats = self.get_statistics_sync()
        if workflow_id:
            filtered = [h for h in _ai_history if h.get("workflow_id") == workflow_id]
            return {"workflow_id": workflow_id, "executions": len(filtered), **stats.get("kpi", {})}
        return stats.get("kpi", {})

    def summary(self) -> dict[str, Any]:
        self.initialize()
        return self.registry.summary()

    async def get_statistics(self) -> dict[str, Any]:
        self.initialize()
        from repositories.workflow_execution_repository import WorkflowExecutionRepository
        from database.session import get_session

        try:
            async with get_session() as session:
                db_stats = await WorkflowExecutionRepository(session).get_statistics()
        except Exception:
            db_stats = {}

        total = _success_count + _failure_count
        avg_exec = (
            round(sum(_execution_durations_ms) / len(_execution_durations_ms), 2)
            if _execution_durations_ms
            else db_stats.get("average_execution_time_ms", 0.0)
        )
        avg_step = (
            round(sum(_step_durations_ms) / len(_step_durations_ms), 2) if _step_durations_ms else 0.0
        )

        return {
            "registered_workflows": [w.to_dict() for w in self.registry.list_all()],
            "active_executions": len(workflow_executor.list_active()),
            "completed_today": db_stats.get("completed_today", 0),
            "failed_today": db_stats.get("failed_today", 0),
            "average_execution_time_ms": avg_exec,
            "kpi": {
                "workflow_execution_time_ms": avg_exec,
                "workflow_success_rate": round(_success_count / max(total, 1), 4),
                "workflow_failure_rate": round(_failure_count / max(total, 1), 4),
                "step_execution_time_ms": avg_step,
                "active_workflows": len(workflow_executor.list_active()),
            },
            **db_stats,
        }

    def get_statistics_sync(self) -> dict[str, Any]:
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.get_statistics())
        if loop.is_running():
            return {
                "registered_workflows": [w.to_dict() for w in self.registry.list_all()],
                "active_executions": len(workflow_executor.list_active()),
                "kpi": {},
            }
        return asyncio.run(self.get_statistics())

    def _resolve_definition(self, workflow_id: str, vertical: str | None) -> WorkflowDefinition:
        definition = self.registry.get(workflow_id)
        if definition is None and vertical:
            definition = self.registry.get_for_vertical(vertical)
        if definition is None:
            raise WorkflowNotFoundError(f"Workflow not found: {workflow_id}")
        return definition

    async def _record_execution(self, context: WorkflowContext, result: WorkflowExecutionResult) -> None:
        global _success_count, _failure_count
        for step_result in result.step_results:
            _step_durations_ms.append(step_result.latency_ms)
            if len(_step_durations_ms) > _MAX_SAMPLES:
                del _step_durations_ms[0]
            await publish(
                WorkflowStepCompletedEvent(
                    execution_id=context.execution_id,
                    workflow_id=context.workflow_id,
                    step_id=step_result.step_id,
                    step_type=step_result.step_type,
                    duration_ms=round(step_result.latency_ms, 2),
                    status=result.status,
                )
            )

        if result.status == ExecutionStatus.COMPLETED.value:
            _success_count += 1
            context.status = ExecutionStatus.COMPLETED
            context.completed_at = _utcnow()
            await publish(
                WorkflowCompletedEvent(
                    execution_id=context.execution_id,
                    workflow_id=context.workflow_id,
                    vertical=context.vertical,
                    duration_ms=round(result.latency_ms, 2),
                    request_number=context.request.get("request_number"),
                )
            )
        elif result.status == ExecutionStatus.FAILED.value:
            _failure_count += 1
            context.status = ExecutionStatus.FAILED
            context.error = result.error

        _execution_durations_ms.append(result.latency_ms)
        if len(_execution_durations_ms) > _MAX_SAMPLES:
            del _execution_durations_ms[0]

        await self._persist(context)

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

    async def _persist(self, context: WorkflowContext) -> None:
        from repositories.workflow_execution_repository import WorkflowExecutionRepository
        from database.session import get_session

        try:
            async with get_session() as session:
                await WorkflowExecutionRepository(session).upsert(context)
        except Exception:
            logger.warning("workflow_persist_failed execution=%s", context.execution_id, exc_info=True)

    async def _load(self, execution_id: str) -> WorkflowContext:
        ctx = workflow_executor.get_context(execution_id)
        if ctx is not None:
            return ctx

        from repositories.workflow_execution_repository import WorkflowExecutionRepository
        from database.session import get_session

        async with get_session() as session:
            row = await WorkflowExecutionRepository(session).get_by_id(execution_id)
        if row is None:
            raise WorkflowNotFoundError(f"Workflow execution not found: {execution_id}")
        return WorkflowContext.from_dict(row)


workflow_engine = WorkflowEngine()
