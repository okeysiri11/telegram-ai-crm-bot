# Platform Validation — exceptions.

from __future__ import annotations


class ValidationLayerError(Exception):
    """Base error for validation layer."""


class ValidationFailedError(ValidationLayerError):
    def __init__(self, message: str, *, report_id: str | None = None) -> None:
        super().__init__(message)
        self.report_id = report_id


class ProductionNotReadyError(ValidationLayerError):
    def __init__(self, message: str, issues: list[str] | None = None) -> None:
        super().__init__(message)
        self.issues = issues or []


class StressTestFailedError(ValidationLayerError):
    def __init__(self, scenario: str, message: str) -> None:
        super().__init__(f"Stress test '{scenario}' failed: {message}")
        self.scenario = scenario
