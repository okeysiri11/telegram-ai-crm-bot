# Workflow engine configuration.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowEngineConfig:
    default_max_retries: int = 3
    retry_base_delay_seconds: float = 0.05
    retry_max_delay_seconds: float = 5.0
    default_task_timeout_seconds: float = 300.0
    queue_history_limit: int = 1000


DEFAULT_WORKFLOW_CONFIG = WorkflowEngineConfig()
