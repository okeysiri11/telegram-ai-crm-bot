# RecoveryManager — orchestrate recovery from failures.

from __future__ import annotations

import logging
import time

from platform_reliability.circuit_breaker import CircuitBreaker, circuit_breaker
from platform_reliability.checkpoint_manager import CheckpointManager, checkpoint_manager
from platform_reliability.failover_manager import FailoverManager, failover_manager
from platform_reliability.models import RecoveryAction, RecoveryContext, RecoveryPolicy, RecoveryResult
from platform_reliability.retry_manager import RetryManager, retry_manager

logger = logging.getLogger(__name__)


class RecoveryManager:
    def __init__(
        self,
        *,
        retry: RetryManager | None = None,
        circuit: CircuitBreaker | None = None,
        failover: FailoverManager | None = None,
        checkpoints: CheckpointManager | None = None,
    ) -> None:
        self._retry = retry or retry_manager
        self._circuit = circuit or circuit_breaker
        self._failover = failover or failover_manager
        self._checkpoints = checkpoints or checkpoint_manager
        self._results: list[RecoveryResult] = []

    def reset(self) -> None:
        self._results.clear()

    async def recover(
        self,
        ctx: RecoveryContext,
        *,
        policy: RecoveryPolicy | None = None,
    ) -> RecoveryResult:
        started = time.monotonic()
        policy = policy or RecoveryPolicy()
        circuit_id = f"{ctx.component}:{ctx.agent_id or ctx.tool_id or ctx.workflow_id or 'default'}"

        if policy.circuit_enabled and not self._circuit.allow_request(circuit_id):
            if policy.failover_enabled:
                result = await self._failover_route(ctx)
                result.recovery_time_ms = round((time.monotonic() - started) * 1000, 2)
                self._results.append(result)
                return result
            return RecoveryResult(
                success=False,
                action=RecoveryAction.ISOLATE,
                execution_id=ctx.execution_id,
                message="Circuit open — component isolated",
                recovery_time_ms=round((time.monotonic() - started) * 1000, 2),
            )

        if policy.checkpoint_enabled and ctx.checkpoint_id:
            return await self._restore_checkpoint(ctx, started)

        if ctx.checkpoint_id is None and policy.checkpoint_enabled:
            latest = self._checkpoints.latest_for_workflow(ctx.workflow_id) if ctx.workflow_id else None
            if latest:
                ctx = self._checkpoints.apply_to_context(ctx, latest.checkpoint_id)

        if policy.failover_enabled and ctx.attempt >= policy.max_retries:
            result = await self._failover_route(ctx)
            result.recovery_time_ms = round((time.monotonic() - started) * 1000, 2)
            result.attempts = ctx.attempt
            self._results.append(result)
            return result

        result = RecoveryResult(
            success=True,
            action=RecoveryAction.RETRY,
            execution_id=ctx.execution_id,
            recovered=True,
            attempts=ctx.attempt,
            message="Retry recommended",
            restored_state={
                "shared_context": ctx.shared_context,
                "planning_state": ctx.planning_state,
                "decision_state": ctx.decision_state,
            },
            recovery_time_ms=round((time.monotonic() - started) * 1000, 2),
        )
        self._results.append(result)
        return result

    async def resume_workflow(self, workflow_id: str, *, checkpoint_id: str | None = None) -> RecoveryResult:
        ctx = RecoveryContext(workflow_id=workflow_id, component="workflow")
        if checkpoint_id:
            ctx.checkpoint_id = checkpoint_id
        else:
            latest = self._checkpoints.latest_for_workflow(workflow_id)
            if latest:
                ctx.checkpoint_id = latest.checkpoint_id
        return await self.recover(ctx)

    async def resume_task(self, task_id: str, workflow_id: str | None = None) -> RecoveryResult:
        ctx = RecoveryContext(task_id=task_id, workflow_id=workflow_id, component="task")
        return await self.recover(ctx)

    async def _restore_checkpoint(self, ctx: RecoveryContext, started: float) -> RecoveryResult:
        snapshot = self._checkpoints.restore(ctx.checkpoint_id)  # type: ignore[arg-type]
        ctx = self._checkpoints.apply_to_context(ctx, ctx.checkpoint_id)  # type: ignore[arg-type]
        result = RecoveryResult(
            success=True,
            action=RecoveryAction.CHECKPOINT_RESTORE,
            execution_id=ctx.execution_id,
            recovered=True,
            checkpoint_id=ctx.checkpoint_id,
            message="Restored from checkpoint",
            restored_state=snapshot,
            recovery_time_ms=round((time.monotonic() - started) * 1000, 2),
        )
        self._results.append(result)
        return result

    async def _failover_route(self, ctx: RecoveryContext) -> RecoveryResult:
        if ctx.tool_id:
            return await self._failover.failover_tool(ctx)
        if ctx.agent_id:
            return await self._failover.failover_agent(ctx)
        if ctx.workflow_id:
            return await self._failover.failover_workflow(ctx)
        return await self._failover.graceful_degrade(ctx)


recovery_manager = RecoveryManager()
