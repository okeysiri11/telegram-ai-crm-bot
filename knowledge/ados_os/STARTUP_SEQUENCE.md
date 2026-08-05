---
title: ADOS OS Startup Sequence
aliases:
  - Startup Sequence
  - Boot Sequence
tags:
  - ados-os
  - startup
status: foundation
---

# ADOS OS Startup Sequence

## Purpose

Describe the **complete startup** path from cold boot to Ready—deterministic, observable, and fail-closed on critical faults.

OS: [[ADOS_OS]] · Kernel: [[KERNEL]]

---

## Sequence

```text
Boot
  ↓
Kernel
  ↓
Providers
  ↓
Memory
  ↓
Knowledge
  ↓
Agent Factory
  ↓
Execution Engine
  ↓
Workflows
  ↓
Ready
```

---

## Stage detail

### 1. Boot

- Process starts; load config/edition/flags.  
- Establish logging/audit sink.  
- Create empty Service Registry and Event Bus placeholders.  
- Fail if mandatory config missing.

### 2. Kernel

- Kernel assumes control ([[KERNEL]]).  
- Initialize Module System discovery (manifests only).  
- Prepare dependency validation hooks.  
- Status: Kernel `starting` → Registry entry `ados.kernel`.

### 3. Providers

- Load provider adapters (LLM, VCS, messaging, storage, …).  
- Register each in [[SERVICE_REGISTRY]].  
- Critical provider failure → abort Boot.  
- Optional provider failure → `degraded`, continue.

**Rule:** providers expose capabilities only—no domain init.

### 4. Memory

- [[MEMORY_MANAGER]] allocates short-term/working scopes.  
- Attach long-term/enterprise/project read paths.  
- Emit health for `ados.memory`.

### 5. Knowledge

- Connect Knowledge routing to durable stores (wiki/registries).  
- Validate Knowledge Lead surfaces reachable.  
- Do not mutate knowledge on startup except health pings.  
- Enables later `KnowledgeUpdated` consumers.

### 6. Agent Factory

- Load templates, types, registry.  
- Validate Contract compliance for agents marked auto-start.  
- Register agent services; **Activate** eligible agents → `AgentActivated`.  
- Unhealthy deps → leave agent stopped; log Owner.

See [[../agent_factory/AGENT_FACTORY|AGENT_FACTORY]].

### 7. Execution Engine

- Bind Execution Engine façade to Scheduler + Event Bus.  
- Restore in-flight packages (if any) into correct [[../execution/EXECUTION_STATES|EXECUTION_STATES]].  
- Start [[TASK_SCHEDULER]] workers.  
- Start Orchestrator ([[../agents/ORCHESTRATOR|ORCHESTRATOR]]).

### 8. Workflows

- Register workflow definitions (Feature, Bug Fix, Reviews, …).  
- Map to Execution stages.  
- Module-specific workflows register after core workflows.  
- Modules finish init: capabilities live, health probes green.

### 9. Ready

- Checklist: Kernel, Bus, Registry, Memory, Knowledge routing, Orchestrator, Scheduler, critical providers = healthy.  
- Publish platform Ready signal (event + status).  
- Accept external Requests (Cursor/Telegram/API/GitHub webhooks via adapters).

If checklist fails → stay non-Ready; alert Owners; do not accept production work.

---

## Shutdown (brief)

```text
Drain Scheduler → AgentStopped → Module stop → Providers → Memory flush → Bus flush → Kernel halt
```

Prefer graceful drain so in-flight Packages enter Blocked with reason, not silent loss.

---

## Observability during startup

| Signal | Meaning |
|--------|---------|
| Service HealthChanged | Progressive readiness |
| AgentActivated | Workforce online |
| (absence of Ready) | Do not route Features |

---

## Related

[[MODULE_SYSTEM]] · [[EVENT_BUS]] · [[SERVICE_REGISTRY]] · [[../execution/EXECUTION_ENGINE|EXECUTION_ENGINE]]
