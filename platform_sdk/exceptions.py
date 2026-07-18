# Platform SDK exceptions.

from __future__ import annotations


class PlatformSDKError(Exception):
    """Base error for platform SDK operations."""


class VerticalNotFoundError(PlatformSDKError):
    def __init__(self, code: str) -> None:
        super().__init__(f"Vertical not registered: {code}")
        self.code = code


class VerticalAlreadyRegisteredError(PlatformSDKError):
    def __init__(self, code: str) -> None:
        super().__init__(f"Vertical already registered: {code}")
        self.code = code


class WorkflowNotFoundError(PlatformSDKError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Workflow not found: {name}")
        self.name = name


class ValidationError(PlatformSDKError):
    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class BuildError(PlatformSDKError):
    """Vertical build / wiring failed."""
