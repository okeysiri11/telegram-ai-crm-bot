# Orchestrator configuration — configurable limits and retry policy.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OrchestratorConfig:
    """Runtime configuration for PlatformOrchestrator."""

    default_timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_base_delay_seconds: float = 0.05
    retry_max_delay_seconds: float = 2.0
    enable_fallback: bool = True
    max_queue_length: int = 1000
    message_bus_history_limit: int = 500


DEFAULT_ORCHESTRATOR_CONFIG = OrchestratorConfig()


@dataclass
class RoutingPolicy:
    """Optional per-task routing hints — no hardcoded agent names."""

    capability: str
    fallback_capability: str | None = None
    preferred_agent_id: str | None = None
    min_priority: int = 0
    tags: list[str] = field(default_factory=list)
