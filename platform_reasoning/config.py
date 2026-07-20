# Reasoning engine configuration.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReasoningEngineConfig:
    default_strategy: str = "fast_heuristic"
    debug_mode: bool = False
    max_steps: int = 20
    max_depth: int = 5
    session_history_limit: int = 500
    timeout_seconds: float = 30.0


DEFAULT_REASONING_CONFIG = ReasoningEngineConfig()
