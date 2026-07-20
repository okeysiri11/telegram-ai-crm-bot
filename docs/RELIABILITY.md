# Platform Reliability & Recovery Layer

> Sprint 5.3 — fault tolerance, automatic recovery, and resilient execution

## Overview

The Platform Reliability & Recovery Layer provides **enterprise-grade fault tolerance** with configurable retries, circuit breakers, failover, checkpointing, and automatic recovery across the AI platform.

**No modifications to Sprint 1–5.2 architecture.**

---

## Architecture

```mermaid
flowchart TB
    subgraph Reliability Layer
        RM[ReliabilityManager]
        RYM[RetryManager]
        CB[CircuitBreaker]
        FM[FailoverManager]
        CM[CheckpointManager]
        RCM[RecoveryManager]
        HS[HealthSupervisor]
    end

    subgraph Recovery Flow
        RETRY[Retry]
        FAIL[Failover]
        CP[Checkpoint Restore]
        DEG[Graceful Degradation]
    end

    subgraph Integration
        WF[Workflow Engine]
        AI[AI Engines]
        TF[Tool Framework]
        OBS[Observability]
        SEC[Security Layer]
        AR[Agent Registry]
        OR[Orchestrator]
    end

    RM --> RYM
    RM --> CB
    RM --> RCM --> FM
    RM --> CM
    RM --> HS
    RCM --> Recovery Flow
    RM -.-> Integration
```

---

## Core Components

| Component | Role |
|-----------|------|
| `ReliabilityManager` | Unified reliability entry point |
| `RetryManager` | Exponential/linear/fixed retry with backoff |
| `CircuitBreaker` | Closed / open / half-open fault isolation |
| `FailoverManager` | Alternative agent, tool, workflow selection |
| `CheckpointManager` | Workflow/task snapshots and restore |
| `RecoveryManager` | Recovery orchestration |
| `HealthSupervisor` | Continuous monitoring and auto-recovery |
| `RecoveryPolicy` | Configurable retry, circuit, failover, checkpoint settings |
| `RecoveryContext` | Execution state for recovery decisions |
| `RecoveryResult` | Recovery outcome with restored state |

---

## Retry Engine

| Strategy | Delay Formula |
|----------|---------------|
| Exponential | `base × 2^(attempt-1)` |
| Linear | `base × attempt` |
| Fixed | `base` |

- Configurable max retries
- Retry conditions (`timeout`, `transient`, `unavailable`)
- Retry metrics (success rate, avg attempts)

---

## Circuit Breaker

| State | Behavior |
|-------|----------|
| Closed | Normal operation; failures counted |
| Open | Requests blocked after threshold |
| Half-open | Probe after recovery timeout |

- Configurable failure threshold
- Recovery timeout with automatic half-open
- Manual reset via `reset_circuit()`
- Event log for breaker transitions

---

## Failover

| Type | Description |
|------|-------------|
| Agent failover | Select alternative agent from registry or registered fallbacks |
| Tool failover | Use registered fallback tools |
| Workflow failover | Execute fallback workflow path |
| Graceful degradation | Reduced functionality when no fallback available |

Register fallbacks: `reliability_manager.register_fallback("primary", ["alt1", "alt2"])`

---

## Checkpointing

- Save workflow/task execution snapshots
- Restore shared context, planning state, decision state
- Rollback to latest workflow checkpoint
- Configurable retention limit

---

## Recovery Flow

1. Detect failure (retry exhausted, circuit open, or explicit recovery)
2. Attempt checkpoint restore if available
3. Restore planning/decision/shared context
4. Failover to alternative agent/tool/workflow if configured
5. Graceful degradation as last resort
6. Record metrics and emit events
7. Log to observability and learning engines

---

## Health Supervision

- Continuous component health checks via Observability Layer
- Automatic isolation of unhealthy components
- Automatic recovery attempts
- Recovery reports with component status

---

## Metrics

`reliability_manager.metrics_summary()` returns:

| Metric | Description |
|--------|-------------|
| `recovery_success_rate` | Successful recoveries |
| `retry_count` | Total retry operations |
| `circuit_breaker_events` | Breaker state transitions |
| `avg_recovery_latency_ms` | Average recovery time |
| `availability` | Success ratio |
| `mttr_ms` | Mean time to recover |
| `failure_frequency` | Total failures recorded |

---

## Usage

### Execute with reliability wrapper

```python
from platform_reliability import reliability_manager, RecoveryContext, RecoveryPolicy

ctx = RecoveryContext(workflow_id="wf-1", agent_id="auto_agent", component="workflow")
policy = RecoveryPolicy(max_retries=3, retry_strategy="exponential")

result = await reliability_manager.execute_with_reliability(
    my_async_function,
    ctx=ctx,
    policy=policy,
    circuit_id="workflow:auto_agent",
)
```

### Checkpoints

```python
cp = reliability_manager.save_checkpoint(
    workflow_id="wf-1",
    step_index=3,
    snapshot={
        "shared_context": {"user": "123"},
        "planning_state": {"plan_id": "p1"},
        "decision_state": {"decision_id": "d1"},
    },
)
result = await reliability_manager.resume_workflow("wf-1")
```

### Circuit breaker

```python
state = reliability_manager.circuit_state("tool:crm_lookup")
reliability_manager.reset_circuit("tool:crm_lookup")
```

### Health supervision

```python
report = await reliability_manager.supervise_health()
print(report["isolated"], report["recoveries"])
```

---

## Integration Bridges

| Layer | Bridge |
|-------|--------|
| Workflow | `checkpoint_from_workflow()` |
| Planning | `restore_planning_state()` |
| Decision | `restore_decision_state()` |
| Learning | `record_learning_from_failure()` |
| Observability | `observability_log_recovery()` |
| Security | `secure_recovery()` |
| Agents | `orchestrator_failover()` |

---

## Events

| Event | When |
|-------|------|
| `RecoveryStartedEvent` | Recovery begins |
| `RecoveryCompletedEvent` | Recovery finished |
| `CircuitStateChangedEvent` | Breaker state change |
| `CheckpointSavedEvent` | Checkpoint stored |
| `FailoverTriggeredEvent` | Failover activated |

---

## Developer Guide

1. Wrap critical async operations with `execute_with_reliability()`
2. Save checkpoints at workflow step boundaries
3. Register fallback agents/tools for failover
4. Configure `RecoveryPolicy` per operation type
5. Monitor `metrics_summary()` and circuit states
6. Run `supervise_health()` on a schedule
7. Use half-open circuit recovery for automatic healing

Package location: `platform_reliability/`

Tests: `tests/test_reliability_layer.py`
