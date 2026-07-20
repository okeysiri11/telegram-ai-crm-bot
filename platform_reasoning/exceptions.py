# Reasoning engine exceptions.

from __future__ import annotations


class ReasoningError(Exception):
    def __init__(self, message: str, *, code: str = "reasoning_error") -> None:
        super().__init__(message)
        self.code = code


class ReasoningSessionNotFoundError(ReasoningError):
    def __init__(self, session_id: str) -> None:
        super().__init__(f"Reasoning session not found: {session_id}", code="session_not_found")
        self.session_id = session_id


class ReasoningStrategyNotFoundError(ReasoningError):
    def __init__(self, strategy: str) -> None:
        super().__init__(f"Reasoning strategy not found: {strategy}", code="strategy_not_found")
        self.strategy = strategy


class ReasoningPipelineError(ReasoningError):
    def __init__(self, step: str, message: str) -> None:
        super().__init__(f"Pipeline step '{step}' failed: {message}", code="pipeline_error")
        self.step = step
