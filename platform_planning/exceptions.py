# Planning engine exceptions.

from __future__ import annotations


class PlanningError(Exception):
    def __init__(self, message: str, *, code: str = "planning_error") -> None:
        super().__init__(message)
        self.code = code


class PlanNotFoundError(PlanningError):
    def __init__(self, plan_id: str) -> None:
        super().__init__(f"Plan not found: {plan_id}", code="plan_not_found")
        self.plan_id = plan_id


class PlanValidationError(PlanningError):
    def __init__(self, message: str, *, details: list[str] | None = None) -> None:
        super().__init__(message, code="plan_validation_error")
        self.details = details or []


class ReplanningError(PlanningError):
    def __init__(self, plan_id: str, step_id: str, message: str) -> None:
        super().__init__(message, code="replanning_error")
        self.plan_id = plan_id
        self.step_id = step_id
