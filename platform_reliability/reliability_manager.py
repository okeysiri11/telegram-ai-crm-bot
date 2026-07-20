# ReliabilityManager — unified fault tolerance and recovery entry point.

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from events.publisher import publish
from platform_reliability.checkpoint_manager import CheckpointManager, checkpoint_manager
from platform_reliability.circuit_breaker import CircuitBreaker, circuit_breaker
from platform_reliability.config import DEFAULT_RELIABILITY_CONFIG, ReliabilityConfig
from platform_reliability.failover_manager import FailoverManager, failover_manager
from platform_reliability.health_supervisor import HealthSupervisor, health_supervisor
from platform_reliability.integrations import ReliabilityIntegrations, reliability_integrations
from platform_reliability.metrics import ReliabilityMetrics, reliability_metrics
from platform_reliability.models import Checkpoint, RecoveryContext, RecoveryPolicy, RecoveryResult, RetryResult
from platform_reliability.recovery_manager import RecoveryManager, recovery_manager
from platform_reliability.reliability_events import (
    CheckpointSavedEvent,
    CircuitStateChangedEvent,
    FailoverTriggeredEvent,
    RecoveryCompletedEvent,
    RecoveryStartedEvent,
)
from platform_reliability.retry_manager import RetryManager, retry_manager

logger = logging.getLogger(__name__)


class ReliabilityManager:
    """Enterprise-grade fault tolerance and automatic recovery facade."""

    def __init__(
        self,
        *,
        retry: RetryManager | None = None,
        circuit: CircuitBreaker | None = None,
        recovery: RecoveryManager | None = None,
        failover: FailoverManager | None = None,
        checkpoints: CheckpointManager | None = None,
        supervisor: HealthSupervisor | None = None,
        metrics: ReliabilityMetrics | None = None,
        integrations: ReliabilityIntegrations | None = None,
        config: ReliabilityConfig | None = None,
    ) -> None:
        self._retry = retry or retry_manager
        self._circuit = circuit or circuit_breaker
        self._recovery = recovery or recovery_manager
        self._failover = failover or failover_manager
        self._checkpoints = checkpoints or checkpoint_manager
        self._supervisor = supervisor or health_supervisor
        self._metrics = metrics or reliability_metrics
        self._integrations = integrations or reliability_integrations
        self._config = config or DEFAULT_RELIABILITY_CONFIG

    def reset(self) -> None:
        self._retry.reset()
        self._circuit.reset()
        self._recovery.reset()
        self._failover.reset()
        self._checkpoints.reset()
        self._supervisor.reset()
        self._metrics.reset()

    async def execute_with_reliability(
        self,
        fn: Callable[[], Awaitable[Any]],
        *,
        ctx: RecoveryContext | None = None,
        policy: RecoveryPolicy | None = None,
        circuit_id: str | None = None,
    ) -> Any:
        ctx = ctx or RecoveryContext()
        policy = policy or RecoveryPolicy()
        cid = circuit_id or f"{ctx.component}:{ctx.agent_id or 'default'}"

        await publish(RecoveryStartedEvent(execution_id=ctx.execution_id, component=ctx.component, workflow_id=ctx.workflow_id))

        async def wrapped():
            retry_result = await self._retry.execute_safe(fn, policy=policy, error_type=ctx.error_type)
            if not retry_result.success:
                raise RuntimeError(retry_result.error or "execution failed")
            return retry_result.result

        try:
            if policy.circuit_enabled:
                result = await self._circuit.call(cid, wrapped)
            else:
                result = await wrapped()

            await publish(RecoveryCompletedEvent(execution_id=ctx.execution_id, success=True, action="execute", recovery_time_ms=0))
            return result

        except Exception as exc:
            ctx.error = str(exc)
            ctx.attempt += 1
            self._metrics.record_failure()
            recovery_result = await self._recovery.recover(ctx, policy=policy)
            self._metrics.record_recovery(recovery_result)
            await self._integrations.observability_log_recovery(ctx, recovery_result.to_dict())
            await self._integrations.record_learning_from_failure(ctx, recovery_result.to_dict())

            if recovery_result.failover_target:
                await publish(
                    FailoverTriggeredEvent(
                        execution_id=ctx.execution_id,
                        primary=ctx.agent_id or ctx.tool_id or "unknown",
                        fallback=recovery_result.failover_target,
                    )
                )

            await publish(
                RecoveryCompletedEvent(
                    execution_id=ctx.execution_id,
                    success=recovery_result.success,
                    action=recovery_result.action.value,
                    recovery_time_ms=recovery_result.recovery_time_ms,
                )
            )
            if recovery_result.success and recovery_result.restored_state:
                return recovery_result.restored_state
            raise

    async def recover(self, ctx: RecoveryContext, *, policy: RecoveryPolicy | None = None) -> RecoveryResult:
        result = await self._recovery.recover(ctx, policy=policy)
        self._metrics.record_recovery(result)
        return result

    def save_checkpoint(self, **kwargs) -> Checkpoint:
        cp = self._checkpoints.save(**kwargs)
        return cp

    async def publish_checkpoint(self, cp: Checkpoint) -> None:
        await publish(
            CheckpointSavedEvent(
                checkpoint_id=cp.checkpoint_id,
                workflow_id=cp.workflow_id,
                task_id=cp.task_id,
            )
        )

    async def resume_workflow(self, workflow_id: str, **kwargs) -> RecoveryResult:
        return await self._recovery.resume_workflow(workflow_id, **kwargs)

    async def supervise_health(self) -> dict[str, Any]:
        return await self._supervisor.supervise()

    def register_fallback(self, primary: str, alternatives: list[str]) -> None:
        self._failover.register_fallback(primary, alternatives)

    def circuit_state(self, circuit_id: str) -> str:
        return self._circuit.state(circuit_id).value

    def reset_circuit(self, circuit_id: str) -> None:
        self._circuit.force_reset(circuit_id)

    def metrics_summary(self) -> dict:
        return self._metrics.summary()


reliability_manager = ReliabilityManager()
