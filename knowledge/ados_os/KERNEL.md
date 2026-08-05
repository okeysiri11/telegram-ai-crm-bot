---
title: ADOS Kernel
aliases:
  - Kernel
  - ADOS Kernel
tags:
  - ados-os
  - kernel
status: foundation
---

# ADOS Kernel

## Purpose

The **ADOS Kernel** is the lowest coordination layer of ADOS OS. It **boots**, initializes modules, loads providers, starts the Orchestrator, and brings registries, memory, and the event bus online.

OS overview: [[ADOS_OS]] · Startup: [[STARTUP_SEQUENCE]]

---

## Responsibilities

```text
boot
    → initialize modules
    → load providers
    → start orchestrator
    → register agents
    → register workflows
    → initialize memory
    → initialize event bus
```

(Plus: seed Service Registry health; enter Ready only when critical services report healthy.)

---

## Boot

| Concern | Behavior |
|---------|----------|
| **Entry** | Process/runtime start (CLI, service, or host IDE session acting as OS host) |
| **Config** | Load environment, edition, feature flags—no secrets in knowledge docs |
| **Fail-fast** | Missing critical provider or corrupt registry → abort with clear error |
| **Idempotency** | Re-boot must not double-register the same Service ID without version bump |

---

## Initialize modules

- Discover module manifests (CRM, ERP, Marketplace, …) via [[MODULE_SYSTEM]].  
- Register each module’s services into [[SERVICE_REGISTRY]].  
- Do **not** run business workflows yet—only declare capabilities and dependencies.  
- Respect additive architecture: modules inject; they do not rewrite Core.

---

## Load providers

Providers are **adapters** (LLM, VCS, messaging, storage, telemetry):

| Rule | Detail |
|------|--------|
| Capability only | Chat, embed, push, clone—**no domain rules** |
| Versioned | Provider ID + version in Service Registry |
| Swappable | OpenAI ↔ Claude ↔ local; GitHub ↔ other VCS—via same capability interface |
| Optional | Non-critical providers degrade; critical ones block Ready |

---

## Start orchestrator

- Instantiate ADOS Orchestrator as the coordination service.  
- Bind Orchestrator to Event Bus, Task Scheduler, and Execution Engine façade.  
- Orchestrator does not implement features; it schedules and gates.

See [[../agents/ORCHESTRATOR|ORCHESTRATOR]].

---

## Register agents

- Load agent registry entries from Factory/Knowledge.  
- Activate only agents that pass Contract + Lifecycle gates.  
- Emit `AgentActivated` / skip with reason if unhealthy dependencies.

See [[../agent_factory/AGENT_REGISTRY|AGENT_REGISTRY]] · [[../agent_factory/AGENT_LIFECYCLE|AGENT_LIFECYCLE]].

---

## Register workflows

- Load workflow definitions (New Feature, Bug Fix, Architecture Review, …).  
- Map workflows to Execution Engine stages and [[../execution/EXECUTION_STATES|EXECUTION_STATES]].  
- Publish workflow Service IDs for modules and Orchestrator.

---

## Initialize memory

- Allocate short-term / working scopes for the session.  
- Attach long-term / enterprise / project stores (read paths).  
- Agent memory namespaces keyed by agent ID.

See [[MEMORY_MANAGER]].

---

## Initialize event bus

- Start in-process or distributed bus per deployment mode.  
- Register core event types ([[EVENT_BUS]]).  
- Wire audit/logging consumers before producers flood the bus.

---

## Kernel invariants

1. Providers stay outside business logic.  
2. Service Registry is the source of “what exists.”  
3. Event Bus is the source of “what happened.”  
4. Ready requires: Registry + Bus + Memory + Orchestrator + Scheduler healthy.  
5. Kernel never bypasses Architecture or Security gates.

---

## Related

[[SERVICE_REGISTRY]] · [[EVENT_BUS]] · [[TASK_SCHEDULER]] · [[STARTUP_SEQUENCE]]
