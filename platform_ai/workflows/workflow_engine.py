# AI Workflow Engine facade — delegates to unified platform_workflows runtime.

from __future__ import annotations

from typing import Any

from platform_ai.workflows.models import WorkflowDefinition as AIWorkflowDefinition
from platform_ai.workflows.models import WorkflowExecutionRequest, WorkflowExecutionResult
from platform_ai.workflows.workflow_cache import workflow_cache
from platform_ai.workflows.workflow_metrics import workflow_metrics
from platform_workflows.workflow_engine import WorkflowEngine, workflow_engine
from platform_workflows.workflow_executor import workflow_executor


class AIWorkflowEngine(WorkflowEngine):
    """Compatibility wrapper — same singleton runtime as WorkflowEngine."""

    def reset(self) -> None:
        super().reset()
        workflow_cache.reset()
        workflow_metrics.reset()

    def register(self, definition: AIWorkflowDefinition) -> Any:
        unified = definition.to_unified() if hasattr(definition, "to_unified") else definition
        if hasattr(unified, "steps") and isinstance(getattr(unified, "steps", None), dict):
            super().register(unified)
        else:
            super().register(definition.to_unified())
        from platform_ai.workflows.models import WorkflowRecord, WorkflowState

        return WorkflowRecord(definition=definition, state=WorkflowState.REGISTERED)

    async def execute(self, request: WorkflowExecutionRequest) -> WorkflowExecutionResult:
        if request.use_cache:
            cached = workflow_cache.get(request.workflow_id, request.input)
            if cached:
                workflow_metrics.record(cached)
                return cached
        result = await super().execute(request)
        workflow_metrics.record(result)
        if request.use_cache and result.status == "completed":
            workflow_cache.set(request.workflow_id, request.input, result)
        return result

    def cancel(self, execution_id: str) -> bool:
        return workflow_executor.cancel(execution_id)


ai_workflow_engine = AIWorkflowEngine()

__all__ = ["AIWorkflowEngine", "ai_workflow_engine"]
