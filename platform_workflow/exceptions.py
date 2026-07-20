# Workflow & task engine exceptions.

from __future__ import annotations


class WorkflowEngineError(Exception):
    def __init__(self, message: str, *, code: str = "workflow_error") -> None:
        super().__init__(message)
        self.code = code


class WorkflowNotFoundError(WorkflowEngineError):
    def __init__(self, workflow_id: str) -> None:
        super().__init__(f"Workflow not found: {workflow_id}", code="workflow_not_found")
        self.workflow_id = workflow_id


class TaskNotFoundError(WorkflowEngineError):
    def __init__(self, task_id: str) -> None:
        super().__init__(f"Task not found: {task_id}", code="task_not_found")
        self.task_id = task_id


class InvalidWorkflowStateError(WorkflowEngineError):
    def __init__(self, workflow_id: str, state: str) -> None:
        super().__init__(
            f"Invalid workflow state for {workflow_id}: {state}",
            code="invalid_workflow_state",
        )


class AgentAssignmentError(WorkflowEngineError):
    def __init__(self, capability: str, message: str) -> None:
        super().__init__(message, code="agent_assignment_error")
        self.capability = capability


class HumanAssignmentError(WorkflowEngineError):
    def __init__(self, role: str, message: str) -> None:
        super().__init__(message, code="human_assignment_error")
        self.role = role
