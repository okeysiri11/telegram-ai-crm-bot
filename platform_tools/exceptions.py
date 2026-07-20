# Tool framework exceptions.

from __future__ import annotations


class ToolFrameworkError(Exception):
    def __init__(self, message: str, *, code: str = "tool_error") -> None:
        super().__init__(message)
        self.code = code


class ToolNotFoundError(ToolFrameworkError):
    def __init__(self, tool_id: str) -> None:
        super().__init__(f"Tool not found: {tool_id}", code="tool_not_found")
        self.tool_id = tool_id


class ToolAlreadyRegisteredError(ToolFrameworkError):
    def __init__(self, tool_id: str) -> None:
        super().__init__(f"Tool already registered: {tool_id}", code="tool_already_registered")
        self.tool_id = tool_id


class ToolValidationError(ToolFrameworkError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="tool_validation_error")


class ToolPermissionDeniedError(ToolFrameworkError):
    def __init__(self, tool_id: str, permission: str) -> None:
        super().__init__(
            f"Permission denied for tool {tool_id}: requires {permission}",
            code="tool_permission_denied",
        )
        self.tool_id = tool_id
        self.permission = permission


class ToolExecutionError(ToolFrameworkError):
    def __init__(self, tool_id: str, message: str) -> None:
        super().__init__(message, code="tool_execution_error")
        self.tool_id = tool_id


class ToolTimeoutError(ToolFrameworkError):
    def __init__(self, tool_id: str, timeout_seconds: float) -> None:
        super().__init__(
            f"Tool {tool_id} timed out after {timeout_seconds}s",
            code="tool_timeout",
        )
        self.tool_id = tool_id


class ToolCancelledError(ToolFrameworkError):
    def __init__(self, tool_id: str) -> None:
        super().__init__(f"Tool execution cancelled: {tool_id}", code="tool_cancelled")
        self.tool_id = tool_id
