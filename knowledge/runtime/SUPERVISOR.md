---
title: ADOS Runtime Supervisor
aliases:
  - Supervisor
  - Runtime Supervisor
tags:
  - runtime
  - supervision
status: foundation
---

# ADOS Supervisor

## Purpose

The **Supervisor** monitors the AI Runtime and **intervenes** when agents or providers misbehave—stalls, duplicates, deadlocks, timeouts, memory pressure, and bad retry loops—without replacing Orchestrator planning or Architect/Security authority.

AI Runtime: [[AI_RUNTIME]] · Agent Runtime: [[AGENT_RUNTIME]] · Resources: [[RESOURCE_MANAGER]]

---

## Responsibilities

Detect and act on:

| Detection | Action |
|-----------|--------|
| **Stalled agents** | Missing heartbeats → Suspend/nudge/cancel; open Recovery if checkpoint exists |
| **Duplicate work** | Same Package-ID + overlapping unit ownership → stop duplicate; keep canonical assignee |
| **Deadlocks** | Wait-graph cycle → break edge / serialize / escalate to Orchestrator |
| **Provider failures** | UPP unhealthy/quota storms → pause dependents; rely on failover; degrade queues |
| **Timeout** | Enforce soft/hard timeouts; cancel; log |
| **Memory overflow** | Trim context / Suspend / fail unit; never OOM the host silently |
| **Retry strategy** | Admit Retry Queue only for retryable failures; cap attempts; dead-letter |

---

## Detection signals

- Heartbeats ([[AGENT_COMMUNICATION_PROTOCOL]])  
- Queue age / depth  
- Resource meters (CPU, tokens, cost)  
- Provider health events  
- Dependency wait graphs  
- Duplicate assignment index  
- Execution Log error rates

---

## Intervention ladder

```text
1. Observe & alert
2. Nudge (broadcast / Orchestrator)
3. Suspend Agent Session
4. Cancel / fail unit
5. Escalate (Team Lead → Architect → CEO per Escalation Model)
```

Supervisor **does not** Approve architecture or waive Security Blocks.

---

## Retry strategy (Supervisor policy)

| Failure class | Strategy |
|---------------|----------|
| Transient provider timeout | Retry Queue + backoff; UPP failover |
| Logic / assert / invalid_request | No retry; failure → Rework path |
| Auth expired | One re-auth then retry; else fail |
| Deadlock break | Re-schedule serialized; do not tight-loop |
| Cancel storm | Cooldown before re-admit Emergency/Priority |

---

## Duplicate work policy

- Fingerprint: Package-ID + unit hash + capability.  
- Second starter gets `failure` duplicate; first remains.  
- Interactive clarify sessions exempt if marked consult-only.

---

## Related

[[TASK_QUEUE]] · [[PARALLEL_EXECUTION]] · [[EXECUTION_LOG]] · [[../workforce/ESCALATION_MODEL|ESCALATION_MODEL]] · [[../providers/FAILOVER_SYSTEM|FAILOVER_SYSTEM]]
