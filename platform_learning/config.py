# Learning engine configuration.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LearningEngineConfig:
    default_cycle_limit: int = 100
    min_pattern_occurrences: int = 2
    max_recommendations: int = 10
    failure_repeat_threshold: int = 3
    debug_mode: bool = False


DEFAULT_LEARNING_CONFIG = LearningEngineConfig()
