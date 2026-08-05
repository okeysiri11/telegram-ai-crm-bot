---
title: ADOS Task Scheduler
aliases:
  - Task Scheduler
tags:
  - ados-os
  - scheduling
status: foundation
---

# ADOS Task Scheduler

## Purpose

Describe how ADOS OS **schedules execution units** with priorities, dependencies, parallelism, retries, timeouts, and deadlock prevention.

OS: [[ADOS_OS]] · Parallelism: [[../execution/PARALLEL_EXECUTION|PARALLEL_EXECUTION]] · States: [[../execution/EXECUTION_STATES|EXECUTION_STATES]]

---

## Inputs

- Tasks/Subtasks/Execution Units from [[../execution/TASK_DECOMPOSER|TASK_DECOMPOSER]]  
- Events: `TaskCreated`, `TaskAssigned`, `ReviewApproved`, `TaskUnblocked`, …  
- Service health from [[SERVICE_REGISTRY]]  
- Agent eligibility (`AgentActivated`)

---

## Priority queue

| Priority | Typical use |
|----------|-------------|
| **P0** | Sev-1 incident, security Block follow-up |
| **P1** | Production release-bound critical path |
| **P2** | Normal Feature Tasks |
| **P3** | Docs/Knowledge debt, refactors, Learning |

Rules:

- Higher priority preempts **new** scheduling of lower priority on the same agent/service—not mid-unsafe mutation without Orchestrator policy.  
- Product/CEO may reprioritize; Architect/Security gates still bind.

---

## Dependency scheduler

- Maintain DAG of blocking edges.  
- A unit is **runnable** only when all blocking predecessors are Complete (or waived).  
- Non-blocking (inform) edges do not prevent start; they force re-sync at merge points.  
- On `ReviewApproved` / predecessor Complete → wake dependents.

Aligns with [[../execution/PARALLEL_EXECUTION|PARALLEL_EXECUTION]] waves.

---

## Parallel execution

- Schedule all runnable units whose owners are healthy and not over capacity.  
- Respect per-agent and per-service concurrency limits.  
- Critical-path units get preferential slots within the same priority band.  
- Merge points are scheduler barriers (no Deploying until Ready barriers clear).

---

## Retry policy

| Class | Policy |
|-------|--------|
| Transient infra (provider timeout) | Exponential backoff, capped attempts |
| Flaky test | Limited retry then QA Rework event |
| Logic / Assert failure | **No** blind retry—emit Rework / fail |
| Security denial | No retry; escalate |

Every retry emits audit detail; after exhaustion → dead-letter + Owner.

---

## Timeouts

| Scope | Behavior |
|-------|----------|
| Execution Unit | Soft timeout → warn; hard timeout → mark Blocked/Failed, free agent |
| Review gate | SLA timer → Orchestrator nudge → escalate |
| Deployment | Hard timeout → rollback path / Ops |

Timeouts never silently Approve.

---

## Deadlock prevention

1. **DAG only** — reject cyclic blocking dependencies at schedule time.  
2. **Lock ordering** — shared resources (schema migrate, registry write) acquired in global order.  
3. **Wait graphs** — detect A waits B waits A → break via Orchestrator (cancel edge, escalate, or serialize).  
4. **Lease expiry** — agent leases expire so crashed workers cannot hold the graph forever.  
5. **No hidden waits** — Blocked state must name predecessor Package-ID ([[../execution/EXECUTION_STATES|EXECUTION_STATES]]).

---

## Scheduler ↔ Orchestrator

```text
Orchestrator decides what should exist (packages, gates)
Scheduler decides when runnable units run
Event Bus notifies both of state changes
```

Scheduler does not Approve architecture or security.

---

## Related

[[EVENT_BUS]] · [[KERNEL]] · [[../execution/DECISION_ENGINE|DECISION_ENGINE]]
