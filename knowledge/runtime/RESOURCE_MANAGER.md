---
title: ADOS Runtime Resource Manager
aliases:
  - Resource Manager
tags:
  - runtime
  - resources
status: foundation
---

# ADOS Resource Manager

## Purpose

Describe how the AI Runtime **allocates and limits** compute, memory, LLM/provider usage, concurrency, rate limits, and cost—so agents cannot starve the platform or unbounded-spend.

AI Runtime: [[AI_RUNTIME]] · UPP: [[../providers/UNIVERSAL_PROVIDER_PLATFORM|UPP]] · Failover: [[../providers/FAILOVER_SYSTEM|FAILOVER_SYSTEM]]

---

## Resource dimensions

### CPU allocation

- Per-agent and per-queue CPU shares.  
- Background limited; Emergency elevated.  
- Supervisor may Suspend on sustained peg.

### Memory allocation

- Working/session memory caps; context bundle size budgets ([[../memory/CONTEXT_ENGINE|CONTEXT_ENGINE]]).  
- Overflow → truncate low-priority context or Suspend ([[SUPERVISOR]] memory overflow).  
- Distinct from host RAM policy vs Enterprise Memory durability.

### LLM usage

- Tokens in/out budgets per Package-ID, tenant, agent, and time window.  
- Model-class quotas (reasoning vs chat).  
- Exhaustion → defer, downgrade capability class, or fail with clear error—not silent quality drop without log.

### Provider usage

- Concurrent UPP calls per Provider ID.  
- Respect provider health and quota signals.  
- Route through Provider Router; Resource Manager enforces local ceilings.

### Concurrency

- Max Running instances globally, per agent role, per Project.  
- Parallel Execution only within admitted slots ([[PARALLEL_EXECUTION]]).

### Rate limiting

- Per-tenant / per-capability / per-provider request rates.  
- Interactive vs Background different ceilings.  
- 429/quota from UPP → Retry Queue + backoff.

### Cost awareness

- Estimate and record cost in [[EXECUTION_LOG]].  
- Soft budget warn; hard budget cancel or require Orchestrator/CEO approval for overrun.  
- Learning uses cost history to improve routing (cheaper capable provider when quality allows).

---

## Allocation lifecycle

```text
Initialize agent instance
    → Reserve CPU / memory / concurrency / budget
    → Running consumes LLM/provider meters
    → Complete / Cancel → release reservations
```

Oversubscription policy: Priority/Emergency > Interactive > Scheduled > Background.

---

## Rules

1. No agent self-raises its hard budget.  
2. Cost and tokens are first-class log fields.  
3. Resource denial is explicit (Waiting/deferred), not hang.  
4. Security-sensitive capabilities may have separate stricter pools.

---

## Related

[[SESSION_MANAGER]] · [[TASK_QUEUE]] · [[SUPERVISOR]] · [[../providers/PROVIDER_ROUTER|PROVIDER_ROUTER]]
