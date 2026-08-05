---
title: ADOS Runtime Task Queue
aliases:
  - Task Queue
  - Runtime Queues
tags:
  - runtime
  - queue
status: foundation
---

# ADOS Task Queue (Runtime)

## Purpose

Describe the **runtime queues** that feed Agent Runtime. Enterprise priority bands also exist on the OS Task Scheduler; this document defines **queue classes** the AI Runtime uses for admission and dispatch.

AI Runtime: [[AI_RUNTIME]] · OS Scheduler: [[../ados_os/TASK_SCHEDULER|TASK_SCHEDULER]] · Parallelism: [[PARALLEL_EXECUTION]]

---

## Queue classes

### Priority Queue

- Ordered work with explicit P0–P3 (or finer) priority.  
- Critical-path Feature Tasks and gated production work.  
- Preempts admission of lower queues when resources are scarce (not mid-unsafe mutation without policy).

### Background Queue

- Low urgency: indexing helpers, non-blocking docs drafts, Learning extraction, compaction.  
- Runs when Interactive/Priority/Emergency have spare capacity.  
- Strict cost and concurrency caps.

### Interactive Queue

- User-facing, low-latency sessions (chat, Cursor host turns, Telegram replies).  
- Prefer short Execution Units; long jobs should be re-queued to Priority/Background.  
- Higher heartbeat frequency.

### Scheduled Queue

- Cron / deferred / calendar-triggered units.  
- Materialize into Priority or Background at fire time.  
- Missed windows: policy = run, skip, or escalate.

### Emergency Queue

- Sev-1 incidents, security response, production rollback aids.  
- Highest admission; may preempt Background and soft-preempt Interactive.  
- Always audited; Owner + Ops notified.

### Retry Queue

- Units eligible for retry after transient failure ([[SUPERVISOR]] / UPP failover).  
- Backoff delays; max attempts; non-retryable errors never enter.  
- Dead-letter after exhaustion → Failed + Owner.

---

## Admission flow

```text
Orchestrator / Scheduler assigns unit
    → Classify queue
    → Resource Manager admits or defers
    → Agent Runtime: Waiting → Running
```

---

## Rules

1. Same Package-ID may span queues (e.g. Interactive clarify → Priority build).  
2. Emergency does not skip Architecture/Security gates—only scheduling preference.  
3. Retry Queue preserves original capability and security context.  
4. Queue metrics feed Execution Log and Supervisor (depth, age, starvation).

---

## Related

[[RESOURCE_MANAGER]] · [[AGENT_RUNTIME]] · [[../execution/PARALLEL_EXECUTION|Execution PARALLEL_EXECUTION]]
