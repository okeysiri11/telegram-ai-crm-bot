# Decision engine configuration.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionEngineConfig:
    default_strategy: str = "multi_criteria"
    default_policy: str = "balanced"
    max_candidates: int = 20
    min_confidence_threshold: float = 30.0
    debug_mode: bool = False


DEFAULT_DECISION_CONFIG = DecisionEngineConfig()
