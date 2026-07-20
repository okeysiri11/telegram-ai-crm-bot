# Tool executor configuration — sandbox limits and retry policy.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolExecutorConfig:
    default_timeout_seconds: float = 30.0
    max_memory_mb: int = 256
    max_retries: int = 2
    retry_base_delay_seconds: float = 0.05
    retry_max_delay_seconds: float = 2.0
    max_concurrent_executions: int = 10
    audit_log_limit: int = 1000


DEFAULT_TOOL_CONFIG = ToolExecutorConfig()
