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


@dataclass(frozen=True)
class SemanticMemoryConfig:
    """Semantic search and context assembly tuning."""

    max_context_tokens: int = 4096
    max_memories: int = 20
    similarity_threshold: float = 0.35
    importance_weight: float = 0.3
    recency_weight: float = 0.2
    keyword_fallback_min_score: float = 0.1

    def validate(self) -> None:
        if self.max_context_tokens <= 0:
            raise ValueError("max_context_tokens must be positive")
        if self.max_memories <= 0:
            raise ValueError("max_memories must be positive")
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be in [0, 1]")
        if not 0 <= self.importance_weight <= 1:
            raise ValueError("importance_weight must be in [0, 1]")
        if not 0 <= self.recency_weight <= 1:
            raise ValueError("recency_weight must be in [0, 1]")


DEFAULT_SEMANTIC_CONFIG = SemanticMemoryConfig()
