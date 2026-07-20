# Collaboration engine configuration.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CollaborationEngineConfig:
    default_mode: str = "supervisor_worker"
    default_consensus: str = "weighted_voting"
    max_agents: int = 10
    negotiation_timeout_ms: float = 30000.0
    consensus_timeout_ms: float = 15000.0
    delegation_timeout_ms: float = 60000.0
    debug_mode: bool = False


DEFAULT_COLLABORATION_CONFIG = CollaborationEngineConfig()
