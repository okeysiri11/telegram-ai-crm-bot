# Orchestrator exceptions — structured errors, no crash propagation.

from __future__ import annotations


class OrchestratorError(Exception):
    """Base orchestrator error."""

    def __init__(self, message: str, *, code: str = "orchestrator_error", details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


class AgentNotFoundError(OrchestratorError):
    def __init__(self, agent_id: str) -> None:
        super().__init__(f"Agent not found: {agent_id}", code="agent_not_found", details={"agent_id": agent_id})


class AgentAlreadyRegisteredError(OrchestratorError):
    def __init__(self, agent_id: str) -> None:
        super().__init__(
            f"Agent already registered: {agent_id}",
            code="agent_already_registered",
            details={"agent_id": agent_id},
        )


class CapabilityNotRoutableError(OrchestratorError):
    def __init__(self, capability: str) -> None:
        super().__init__(
            f"No agent registered for capability: {capability}",
            code="capability_not_routable",
            details={"capability": capability},
        )


class TaskValidationError(OrchestratorError):
    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message, code="task_validation_error", details=details)


class TaskTimeoutError(OrchestratorError):
    def __init__(self, task_id: str, timeout_seconds: float) -> None:
        super().__init__(
            f"Task {task_id} timed out after {timeout_seconds}s",
            code="task_timeout",
            details={"task_id": task_id, "timeout_seconds": timeout_seconds},
        )


class TaskCancelledError(OrchestratorError):
    def __init__(self, task_id: str) -> None:
        super().__init__(
            f"Task {task_id} was cancelled",
            code="task_cancelled",
            details={"task_id": task_id},
        )


class TaskRetryExhaustedError(OrchestratorError):
    def __init__(self, task_id: str, attempts: int, last_error: str) -> None:
        super().__init__(
            f"Task {task_id} exhausted {attempts} retries: {last_error}",
            code="task_retry_exhausted",
            details={"task_id": task_id, "attempts": attempts, "last_error": last_error},
        )


class AgentExecutionError(OrchestratorError):
    def __init__(self, agent_id: str, message: str, *, details: dict | None = None) -> None:
        super().__init__(
            message,
            code="agent_execution_error",
            details={"agent_id": agent_id, **(details or {})},
        )
