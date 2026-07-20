# Reliability layer configuration.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReliabilityConfig:
    default_max_retries: int = 3
    default_backoff_base_ms: float = 100.0
    default_backoff_max_ms: float = 30000.0
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout_sec: float = 60.0
    health_check_interval_sec: float = 30.0
    checkpoint_retention_limit: int = 500


DEFAULT_RELIABILITY_CONFIG = ReliabilityConfig()
