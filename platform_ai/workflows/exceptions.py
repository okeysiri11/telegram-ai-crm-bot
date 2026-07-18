# AI Workflow exceptions.

from __future__ import annotations


class WorkflowError(Exception):
    """Base workflow error."""


class WorkflowNotFoundError(WorkflowError):
    def __init__(self, workflow_id: str) -> None:
        super().__init__(f"Workflow not found: {workflow_id}")
        self.workflow_id = workflow_id


class WorkflowValidationError(WorkflowError):
    pass


class WorkflowExecutionError(WorkflowError):
    pass


class WorkflowCancelledError(WorkflowError):
    pass


class WorkflowTimeoutError(WorkflowError):
    pass


class StepExecutionError(WorkflowError):
    def __init__(self, step_id: str, message: str) -> None:
        super().__init__(f"Step {step_id}: {message}")
        self.step_id = step_id
