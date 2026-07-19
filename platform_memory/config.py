# Platform Memory — token limits and assembly configuration.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenLimits:
    """Configurable token budgets for context assembly."""

    max_context_tokens: int = 4096
    max_history_tokens: int = 2048
    max_memory_tokens: int = 1024
    max_profile_tokens: int = 512
    max_business_tokens: int = 512
    max_project_tokens: int = 512
    max_session_tokens: int = 1024
    summarize_threshold_ratio: float = 0.85

    def history_summarize_at(self) -> int:
        return int(self.max_history_tokens * self.summarize_threshold_ratio)

    def validate(self) -> None:
        if self.max_context_tokens <= 0:
            raise ValueError("max_context_tokens must be positive")
        if not 0 < self.summarize_threshold_ratio <= 1:
            raise ValueError("summarize_threshold_ratio must be in (0, 1]")


DEFAULT_TOKEN_LIMITS = TokenLimits()
