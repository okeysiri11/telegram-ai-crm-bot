# Learning engine exceptions.

from __future__ import annotations


class LearningError(Exception):
    def __init__(self, message: str, *, code: str = "learning_error") -> None:
        super().__init__(message)
        self.code = code


class SessionNotFoundError(LearningError):
    def __init__(self, session_id: str) -> None:
        super().__init__(f"Learning session not found: {session_id}", code="session_not_found")
        self.session_id = session_id


class FeedbackValidationError(LearningError):
    def __init__(self, message: str, *, details: list[str] | None = None) -> None:
        super().__init__(message, code="feedback_validation_error")
        self.details = details or []
