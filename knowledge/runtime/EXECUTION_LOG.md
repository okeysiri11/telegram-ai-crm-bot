---
title: ADOS Execution Log
aliases:
  - Execution Log
  - Runtime Execution Log
tags:
  - runtime
  - logging
  - audit
status: foundation
---

# ADOS Execution Log

## Purpose

Describe **runtime execution logging**—who ran, what changed, how long, which provider, review outcome, result, cost, and errors—so recovery, audit, Decision Memory, and Learning all share one correlated history.

AI Runtime: [[AI_RUNTIME]] · Decision Memory: [[../memory/DECISION_MEMORY|DECISION_MEMORY]] · Event Bus: [[../ados_os/EVENT_BUS|EVENT_BUS]]

---

## Logged fields

| Field | Content |
|-------|---------|
| **who executed** | Agent ID, session id, user/actor, Orchestrator ref |
| **what changed** | Modules/artifacts refs, handoff summary, graph node ids |
| **duration** | Queue wait + Running time + Review wait |
| **provider** | Provider ID(s), capability, failover_count |
| **review** | Reviewer, disposition, findings refs |
| **result** | Completed \| Failed \| Cancelled \| Suspended outcome |
| **cost** | Tokens, estimated currency, budget remaining |
| **errors** | Normalized codes, messages (redacted), retry count |

Always include: **Package-ID**, timestamps, queue class, resource pool.

---

## Log record (logical)

```text
Log ID:        …
Package-ID:    …
Agent Session: …
Who:           …
What:          […]
Duration:      { queue_ms, run_ms, review_ms }
Provider:      [{ id, capability, … }]
Review:        { … } | null
Result:        completed
Cost:          { tokens_in, tokens_out, amount }
Errors:        []
Security:      tenant, classification
```

---

## When to write

| Moment | Write |
|--------|-------|
| Admit / start Running | Partial start record |
| Provider call boundary | Provider + cost deltas (no secrets) |
| Handoff / Complete | What changed |
| Review disposition | Review fields |
| Terminal state | Final result + totals |
| Supervisor intervene | Error/reason + action |

---

## Retention & use

- Feeds Recovery Session rehydration.  
- Promotes summaries into Decision Memory / Learning (not raw dumps of prompts with secrets).  
- Supports audit for Security Lead.  
- Cost history informs Resource Manager policies.

---

## Redaction rules

- Never log API keys, tokens, raw regulated payloads.  
- Prompt bodies optional and classified; default off in production.  
- Customer PII minimized.

---

## Related

[[SUPERVISOR]] · [[SESSION_MANAGER]] · [[../memory/LEARNING_ENGINE|Memory LEARNING_ENGINE]] · [[../execution/LEARNING_ENGINE|Execution LEARNING_ENGINE]]
