# Decision engine exceptions.

from __future__ import annotations


class DecisionError(Exception):
    def __init__(self, message: str, *, code: str = "decision_error") -> None:
        super().__init__(message)
        self.code = code


class NoCandidatesError(DecisionError):
    def __init__(self) -> None:
        super().__init__("No decision candidates provided", code="no_candidates")


class DecisionValidationError(DecisionError):
    def __init__(self, message: str, *, details: list[str] | None = None) -> None:
        super().__init__(message, code="decision_validation_error")
        self.details = details or []


class PolicyNotFoundError(DecisionError):
    def __init__(self, policy_id: str) -> None:
        super().__init__(f"Decision policy not found: {policy_id}", code="policy_not_found")
        self.policy_id = policy_id
