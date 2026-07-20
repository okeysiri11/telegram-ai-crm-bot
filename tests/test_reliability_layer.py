"""Tests — Platform Reliability & Recovery Layer (Sprint 5.3)."""

from __future__ import annotations

import asyncio

import pytest

from platform_reliability.circuit_breaker import CircuitBreaker
from platform_reliability.checkpoint_manager import CheckpointManager
from platform_reliability.exceptions import CircuitOpenError, CheckpointNotFoundError, MaxRetriesExceededError
from platform_reliability.failover_manager import FailoverManager
from platform_reliability.metrics import ReliabilityMetrics
from platform_reliability.models import (
    CircuitState,
    RecoveryContext,
    RecoveryPolicy,
    RetryStrategy,
)
from platform_reliability.recovery_manager import RecoveryManager
from platform_reliability.reliability_manager import ReliabilityManager
from platform_reliability.retry_manager import RetryManager


@pytest.fixture
def manager() -> ReliabilityManager:
    retry = RetryManager()
    circuit = CircuitBreaker()
    checkpoints = CheckpointManager()
    failover = FailoverManager()
    mgr = ReliabilityManager(
        retry=retry,
        circuit=circuit,
        recovery=RecoveryManager(retry=retry, circuit=circuit, failover=failover, checkpoints=checkpoints),
        failover=failover,
        checkpoints=checkpoints,
        metrics=ReliabilityMetrics(),
    )
    yield mgr
    mgr.reset()


@pytest.mark.asyncio
async def test_exponential_retry_success(manager: ReliabilityManager):
    attempts = {"n": 0}

    async def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise TimeoutError("transient")
        return "ok"

    policy = RecoveryPolicy(max_retries=5, retry_strategy=RetryStrategy.EXPONENTIAL, backoff_base_ms=1.0)
    result = await manager._retry.execute_safe(flaky, policy=policy)
    assert result.success
    assert result.attempts == 3


@pytest.mark.asyncio
async def test_linear_retry_delay():
    rm = RetryManager()
    policy = RecoveryPolicy(retry_strategy=RetryStrategy.LINEAR, backoff_base_ms=100.0)
    assert rm.compute_delay_ms(2, policy) == 200.0


@pytest.mark.asyncio
async def test_max_retries_exceeded():
    rm = RetryManager()

    async def always_fail():
        raise RuntimeError("fail")

    policy = RecoveryPolicy(max_retries=2, backoff_base_ms=1.0)
    result = await rm.execute_safe(always_fail, policy=policy)
    assert not result.success


@pytest.mark.asyncio
async def test_retry_conditions():
    rm = RetryManager()
    policy = RecoveryPolicy(retry_on=["timeout"])
    assert rm.should_retry("timeout", policy)
    assert not rm.should_retry("permanent", policy)


@pytest.mark.asyncio
async def test_circuit_breaker_opens(manager: ReliabilityManager):
    cid = "test:circuit"
    for _ in range(5):
        manager._circuit.record_failure(cid)
    assert manager._circuit.state(cid) == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_blocks_call(manager: ReliabilityManager):
    cid = "test:block"
    for _ in range(5):
        manager._circuit.record_failure(cid)

    async def fn():
        return "ok"

    with pytest.raises(CircuitOpenError):
        await manager._circuit.call(cid, fn)


@pytest.mark.asyncio
async def test_circuit_half_open_recovery(manager: ReliabilityManager):
    cb = manager._circuit
    cid = "test:half"
    for _ in range(5):
        cb.record_failure(cid)
    cb._circuits[cid].opened_at = 0  # force timeout elapsed
    assert cb.allow_request(cid)


@pytest.mark.asyncio
async def test_circuit_manual_reset(manager: ReliabilityManager):
    cid = "test:reset"
    for _ in range(5):
        manager._circuit.record_failure(cid)
    manager.reset_circuit(cid)
    assert manager.circuit_state(cid) == "closed"


@pytest.mark.asyncio
async def test_failover_agent(manager: ReliabilityManager):
    manager.register_fallback("agent_a", ["agent_b"])
    ctx = RecoveryContext(agent_id="agent_a", execution_id="exec-1")
    result = await manager._failover.failover_agent(ctx)
    assert result.success
    assert result.failover_target == "agent_b"


@pytest.mark.asyncio
async def test_failover_tool(manager: ReliabilityManager):
    manager.register_fallback("tool_a", ["tool_b"])
    ctx = RecoveryContext(tool_id="tool_a")
    result = await manager._failover.failover_tool(ctx)
    assert result.failover_target == "tool_b"


@pytest.mark.asyncio
async def test_graceful_degradation(manager: ReliabilityManager):
    ctx = RecoveryContext(error="total failure")
    result = await manager._failover.graceful_degrade(ctx)
    assert result.success
    assert result.restored_state.get("degraded")


@pytest.mark.asyncio
async def test_checkpoint_save_and_restore(manager: ReliabilityManager):
    cp = manager.save_checkpoint(
        workflow_id="wf-1",
        task_id="task-1",
        step_index=2,
        snapshot={"shared_context": {"key": "value"}, "planning_state": {"plan_id": "p1"}},
    )
    restored = manager._checkpoints.restore(cp.checkpoint_id)
    assert restored["shared_context"]["key"] == "value"


@pytest.mark.asyncio
async def test_checkpoint_apply_to_context(manager: ReliabilityManager):
    cp = manager.save_checkpoint(
        workflow_id="wf-2",
        snapshot={"shared_context": {"x": 1}, "planning_state": {}, "decision_state": {"d": 1}},
    )
    ctx = RecoveryContext(workflow_id="wf-2")
    ctx = manager._checkpoints.apply_to_context(ctx, cp.checkpoint_id)
    assert ctx.shared_context["x"] == 1
    assert ctx.decision_state["d"] == 1


@pytest.mark.asyncio
async def test_checkpoint_not_found(manager: ReliabilityManager):
    with pytest.raises(CheckpointNotFoundError):
        manager._checkpoints.get("missing")


@pytest.mark.asyncio
async def test_resume_workflow(manager: ReliabilityManager):
    manager.save_checkpoint(workflow_id="wf-resume", snapshot={"step": 3})
    result = await manager.resume_workflow("wf-resume")
    assert result.action.value in ("checkpoint_restore", "retry")


@pytest.mark.asyncio
async def test_recovery_with_checkpoint(manager: ReliabilityManager):
    cp = manager.save_checkpoint(workflow_id="wf-rec", snapshot={"data": True})
    ctx = RecoveryContext(workflow_id="wf-rec", checkpoint_id=cp.checkpoint_id)
    result = await manager.recover(ctx)
    assert result.success
    assert result.checkpoint_id == cp.checkpoint_id


@pytest.mark.asyncio
async def test_execute_with_reliability_success(manager: ReliabilityManager):
    async def ok():
        return {"status": "done"}

    result = await manager.execute_with_reliability(ok)
    assert result["status"] == "done"


@pytest.mark.asyncio
async def test_metrics_summary(manager: ReliabilityManager):
    ctx = RecoveryContext(workflow_id="wf-m")
    cp = manager.save_checkpoint(workflow_id="wf-m", snapshot={})
    ctx.checkpoint_id = cp.checkpoint_id
    await manager.recover(ctx)
    summary = manager.metrics_summary()
    assert summary["recovery_success_rate"] >= 0


def test_retry_metrics():
    rm = RetryManager()
    rm._record(2, True, 100.0)
    rm._record(3, False, 200.0)
    m = rm.metrics()
    assert m["retries"] == 2


def test_recovery_policy_to_dict():
    policy = RecoveryPolicy(policy_id="test", max_retries=5)
    d = policy.to_dict()
    assert d["policy_id"] == "test"
    assert d["max_retries"] == 5
