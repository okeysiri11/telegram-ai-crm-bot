---
title: ADOS Agent Runtime
aliases:
  - Agent Runtime
tags:
  - runtime
  - agents
  - lifecycle
status: foundation
---

# ADOS Agent Runtime

## Purpose

Describe the **lifecycle of an agent instance** inside the AI Runtime—from creation through archive—including timeout and cancellation rules.

AI Runtime: [[AI_RUNTIME]] · Factory lifecycle: [[../agent_factory/AGENT_LIFECYCLE|AGENT_LIFECYCLE]] · Execution states: [[../execution/EXECUTION_STATES|EXECUTION_STATES]]

---

## Instance lifecycle

```text
Created
    ↓
Initialized
    ↓
Waiting
    ↓
Running
    ↓
Review
    ↓
Completed
    ↓
Archived
```

(Branches: Running/Waiting → **Cancelled** or **Failed** → recover or Archived; Review → Rework → Waiting/Running.)

---

## State definitions

| State | Meaning |
|-------|---------|
| **Created** | Instance record minted; bound to Agent ID + optional Package-ID |
| **Initialized** | Session attached, context bundle loaded, resources reserved |
| **Waiting** | In queue or blocked on dependency / approval |
| **Running** | Actively executing (tools, UPP calls, reasoning) |
| **Review** | Deliverable submitted; awaiting Review/Approval gate |
| **Completed** | Unit/Task done criteria met for this instance |
| **Archived** | Logs flushed; resources released; personal temp memory flushed |

### Side states

| State | Meaning |
|-------|---------|
| **Cancelled** | Stop requested; cleanup done |
| **Failed** | Terminal error after retries / Supervisor decision |
| **Suspended** | Supervisor paused (stall, cost, deadlock investigation) |

---

## Timeout rules

| Scope | Rule |
|-------|------|
| **Running soft timeout** | Warn Orchestrator/Supervisor; allow finish-current-step |
| **Running hard timeout** | Force cancel → Failed/Cancelled; free resources |
| **Waiting dependency timeout** | Escalate; mark Task Blocked with named predecessor |
| **Review SLA timeout** | Nudge reviewers; escalate per Decision Engine |
| **Heartbeat timeout** | Treat as stalled ([[SUPERVISOR]]) |

Timeouts never auto-Approve architecture or security.

---

## Cancellation

### Cooperative cancel

1. Signal `cancel` via [[AGENT_COMMUNICATION_PROTOCOL]].  
2. Agent checkpoints; stops new UPP calls.  
3. Partial artifacts marked incomplete; log `cancelled`.  
4. Resources released → Archived or Failed per policy.

### Forced cancel

1. Supervisor/Orchestrator kills slot after grace.  
2. Provider streams aborted via UPP.  
3. Session → Recovery Session if resume possible.  
4. Execution Log records actor and reason.

Cancellation may originate from: User, Orchestrator, Supervisor, Resource Manager (budget), Security Block.

---

## Mapping to Factory & Execution

| Agent Runtime | Factory | Execution package |
|---------------|---------|-------------------|
| Created–Initialized | Activate instance | Task Assigned |
| Waiting–Running | Operate | In Progress / Blocked |
| Review | — | Review / QA |
| Completed | — | stage Complete |
| Archived | optional Stop | Learning / Archived |

Factory **role** lifecycle ≠ every **instance** run; one agent role spawns many runtime instances.

---

## Related

[[TASK_QUEUE]] · [[SESSION_MANAGER]] · [[RESOURCE_MANAGER]] · [[EXECUTION_LOG]]
