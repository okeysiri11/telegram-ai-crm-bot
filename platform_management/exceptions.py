# Management API exceptions — thin error types for orchestration layer.

from __future__ import annotations


class ManagementAPIError(Exception):
    def __init__(self, message: str, *, status: int = 400, code: str = "management_error") -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code


class ManagementPermissionError(ManagementAPIError):
    def __init__(self, message: str = "Insufficient management API permissions") -> None:
        super().__init__(message, status=403, code="permission_denied")


class ManagementNotFoundError(ManagementAPIError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status=404, code="not_found")
