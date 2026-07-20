# Planning engine configuration.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanningEngineConfig:
    default_strategy: str = "dependency_aware"
    max_steps: int = 20
    max_candidates: int = 5
    default_cost_per_step: float = 1.0
    replanning_enabled: bool = True


DEFAULT_PLANNING_CONFIG = PlanningEngineConfig()
