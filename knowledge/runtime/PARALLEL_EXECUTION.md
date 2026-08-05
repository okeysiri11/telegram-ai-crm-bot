---
title: ADOS Runtime Parallel Execution
aliases:
  - Runtime Parallel Execution
tags:
  - runtime
  - parallelism
status: foundation
---

# ADOS Parallel Execution (Runtime)

## Purpose

Describe **how the AI Runtime runs work concurrently**—independent, parallel, and sequential modes—using dependency graphs, blocking tasks, and synchronization barriers.

Complements enterprise planning in [[../execution/PARALLEL_EXECUTION|Execution PARALLEL_EXECUTION]]. This doc is the **runtime dispatch** view.

AI Runtime: [[AI_RUNTIME]] · Queues: [[TASK_QUEUE]] · Resources: [[RESOURCE_MANAGER]]

---

## Execution modes

### Independent execution

- Units with no edges to in-flight peers.  
- Fully concurrent subject to Resource Manager caps.  
- Typical: unrelated Background indexing vs Interactive chat.

### Parallel execution

- Multiple units of the same Package-ID with **no blocking edge** between them.  
- Example: Frontend against frozen contract ∥ Security threat model.  
- Shared Session carries contract refs; merge still required.

### Sequential execution

- Strict successor after predecessor Complete.  
- Example: Architect Proceed → Backend implement.  
- Enforced by dependency graph + Waiting state.

---

## Dependency graph

- Runtime holds the runnable DAG subset for admitted units.  
- Mirrors Execution Engine blocking/inform edges.  
- Cycle detection → Supervisor deadlock handling.

---

## Blocking tasks

- Downstream Agent Sessions stay **Waiting**.  
- Named predecessor Package-ID/unit id required.  
- Timeout on block → escalate (not silent spin).

---

## Synchronization barriers

| Barrier | Runtime behavior |
|---------|------------------|
| **Design barrier** | No build agents Running until Architect Proceed |
| **Contract barrier** | UI agents may wait or run provisional; integration waits for freeze |
| **Integration barrier** | All parallel build sessions Complete before Review wave |
| **Quality barrier** | QA before Docs claim verified |
| **Release barrier** | Ready before Deploy-related agents |

Barriers are Scheduler/Runtime join points; Approvals still come from Decision authorities.

---

## Dispatch algorithm (summary)

```text
While resources available:
  Select runnable units (deps satisfied) from eligible queues
  Prefer Emergency > Priority > Interactive > Scheduled > Background
  Prefer critical-path within band
  Start Agent Sessions in parallel up to concurrency caps
```

---

## Related

[[SUPERVISOR]] · [[AGENT_RUNTIME]] · [[../execution/TASK_DECOMPOSER|TASK_DECOMPOSER]]
