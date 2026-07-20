# Reliability domain models.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable


class RetryStrategy(str, Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class RecoveryAction(str, Enum):
    RETRY = "retry"
    FAILOVER = "failover"
    CHECKPOINT_RESTORE = "checkpoint_restore"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    ISOLATE = "isolate"


@dataclass
class RecoveryPolicy:
    policy_id: str = "default"
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_base_ms: float = 100.0
    backoff_max_ms: float = 30000.0
    retry_on: list[str] = field(default_factory=lambda: ["timeout", "transient", "unavailable"])
    circuit_enabled: bool = True
    failover_enabled: bool = True
    checkpoint_enabled: bool = True
    recovery_timeout_sec: float = 120.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "max_retries": self.max_retries,
            "retry_strategy": self.retry_strategy.value,
            "circuit_enabled": self.circuit_enabled,
            "failover_enabled": self.failover_enabled,
        }


@dataclass
class RecoveryContext:
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str | None = None
    task_id: str | None = None
    agent_id: str | None = None
    tool_id: str | None = None
    component: str = "platform"
    error: str = ""
    error_type: str = "transient"
    attempt: int = 0
    checkpoint_id: str | None = None
    shared_context: dict[str, Any] = field(default_factory=dict)
    planning_state: dict[str, Any] = field(default_factory=dict)
    decision_state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "tool_id": self.tool_id,
            "component": self.component,
            "error": self.error,
            "attempt": self.attempt,
            "checkpoint_id": self.checkpoint_id,
        }


@dataclass
class RecoveryResult:
    success: bool = False
    action: RecoveryAction = RecoveryAction.RETRY
    execution_id: str = ""
    recovered: bool = False
    failover_target: str | None = None
    checkpoint_id: str | None = None
    attempts: int = 0
    recovery_time_ms: float = 0.0
    message: str = ""
    restored_state: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "action": self.action.value,
            "execution_id": self.execution_id,
            "recovered": self.recovered,
            "failover_target": self.failover_target,
            "checkpoint_id": self.checkpoint_id,
            "attempts": self.attempts,
            "recovery_time_ms": self.recovery_time_ms,
            "message": self.message,
        }


@dataclass
class Checkpoint:
    checkpoint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str | None = None
    task_id: str | None = None
    agent_id: str | None = None
    step_index: int = 0
    snapshot: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "step_index": self.step_index,
            "created_at": self.created_at,
        }


@dataclass
class RetryResult:
    success: bool
    attempts: int
    result: Any = None
    error: str | None = None
    total_delay_ms: float = 0.0


@dataclass
class CircuitBreakerState:
    circuit_id: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_at: float = 0.0
    opened_at: float = 0.0
    failure_threshold: int = 5
    recovery_timeout_sec: float = 60.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "circuit_id": self.circuit_id,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
        }
