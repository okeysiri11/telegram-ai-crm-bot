# AI Workflow Engine — main entry point for cognitive pipeline orchestration.

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from platform_ai.workflows.exceptions import WorkflowNotFoundError, WorkflowValidationError
from platform_ai.workflows.models import (
    ExecutionStatus,
    WorkflowDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResult,
    WorkflowRecord,
    WorkflowState,
)
from platform_ai.workflows.workflow_builder import workflow_builder
from platform_ai.workflows.workflow_cache import workflow_cache
from platform_ai.workflows.workflow_executor import workflow_executor
from platform_ai.workflows.workflow_metrics import workflow_metrics
from platform_ai.workflows.workflow_registry import workflow_registry

logger = logging.getLogger(__name__)


class AIWorkflowEngine:
    """Orchestrates AI Skills into reusable intelligent pipelines."""

    def __init__(self) -> None:
        self._initialized = False
        self._history: list[dict[str, Any]] = []

    def reset(self) -> None:
        workflow_registry.reset()
        workflow_cache.reset()
        workflow_metrics.reset()
        workflow_executor.reset()
        self._history.clear()
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        from platform_ai.skills.skill_manager import skill_manager

        skill_manager.initialize()
        from platform_ai.workflows import workflow_templates

        workflow_templates.register_all()
        self._initialized = True
        logger.info("ai_workflow_engine_initialized workflows=%d", len(workflow_registry.list_records()))

    def register(self, definition: WorkflowDefinition) -> WorkflowRecord:
        workflow_builder.validate(definition)
        return workflow_registry.register(definition)

    def register_from_dict(self, data: dict[str, Any]) -> WorkflowRecord:
        definition = workflow_builder.from_dict(data)
        return self.register(definition)

    def load(self, workflow_id: str) -> WorkflowRecord:
        self.initialize()
        record = workflow_registry.get_record(workflow_id)
        definition = record.definition
        workflow_builder.validate(definition)
        record.state = WorkflowState.LOADED
        record.loaded_at = datetime.now(timezone.utc).isoformat()
        return record

    async def execute(self, request: WorkflowExecutionRequest) -> WorkflowExecutionResult:
        self.initialize()
        record = workflow_registry.get_record(request.workflow_id)
        if not record.definition.enabled:
            raise WorkflowValidationError(f"Workflow disabled: {request.workflow_id}")

        if request.use_cache:
            cached = workflow_cache.get(request.workflow_id, request.input)
            if cached:
                workflow_metrics.record(cached)
                return cached

        if record.state == WorkflowState.REGISTERED:
            self.load(request.workflow_id)

        definition = record.definition
        result = await workflow_executor.execute(definition, request)

        self._history.append(
            {
                "execution_id": result.execution_id,
                "workflow_id": result.workflow_id,
                "status": result.status,
                "latency_ms": result.latency_ms,
                "cost_usd": result.cost_usd,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        if len(self._history) > 500:
            self._history = self._history[-500:]

        workflow_metrics.record(result)
        if request.use_cache and result.status == ExecutionStatus.COMPLETED.value:
            workflow_cache.set(request.workflow_id, request.input, result)

        return result

    async def resume(self, execution_id: str) -> WorkflowExecutionResult:
        state = workflow_executor.get_state(execution_id)
        if state is None or state.status != ExecutionStatus.PAUSED:
            raise WorkflowNotFoundError(f"No paused execution: {execution_id}")
        definition = workflow_registry.get(state.workflow_id)
        request = WorkflowExecutionRequest(
            workflow_id=state.workflow_id,
            input=state.input,
            plugin_id=state.plugin_id,
            user_id=state.user_id,
            execution_id=execution_id,
            use_cache=False,
        )
        state.status = ExecutionStatus.RUNNING
        return await workflow_executor.execute(definition, request, resume_state=state)

    def cancel(self, execution_id: str) -> bool:
        return workflow_executor.cancel(execution_id)

    def list_workflows(self) -> list[dict[str, Any]]:
        self.initialize()
        return [r.to_dict() for r in workflow_registry.list_records()]

    def list_templates(self) -> list[dict[str, Any]]:
        from platform_ai.workflows.workflow_templates import list_templates

        return list_templates()

    def history(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(reversed(self._history[-limit:]))

    def active(self) -> list[dict[str, Any]]:
        return workflow_executor.list_active()

    def metrics(self, workflow_id: str | None = None) -> dict[str, Any]:
        if workflow_id:
            return workflow_metrics.for_workflow(workflow_id)
        return workflow_metrics.summary()

    def summary(self) -> dict[str, Any]:
        self.initialize()
        return workflow_registry.summary()


ai_workflow_engine = AIWorkflowEngine()
