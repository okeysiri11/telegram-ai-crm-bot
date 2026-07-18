# Unified workflow engine exceptions.

from __future__ import annotations


class WorkflowError(Exception):
    """Base workflow error."""


class WorkflowValidationError(WorkflowError, ValueError):
    """Invalid workflow definition."""


class WorkflowNotFoundError(WorkflowError):
    """Workflow or execution not found."""


class StepExecutionError(WorkflowError):
    def __init__(self, step_id: str, message: str) -> None:
        super().__init__(message)
        self.step_id = step_id


class WorkflowExecutionError(WorkflowError):
    pass


class WorkflowCancelledError(WorkflowError):
    pass


class WorkflowTimeoutError(WorkflowError):
    pass
