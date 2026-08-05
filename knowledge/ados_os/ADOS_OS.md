---
title: ADOS Operating System
aliases:
  - ADOS OS
  - Operating System
tags:
  - ados-os
  - kernel
  - enterprise
status: foundation
---

# ADOS Operating System (ADOS OS)

## Purpose

**ADOS OS** is the core operating system responsible for **coordinating every AI capability inside ADOS**.

It does not replace Enterprise Architecture, the Engineering Organization, the Agent Factory, or domain modules. It provides the **shared runtime spine**: boot, services, events, scheduling, memory, security/user context, and enterprise coordination—so capabilities plug in **without coupling** to each other.

This package is **documentation only**. No existing application code is modified.

Related foundations:

- Architecture rules: project `ados-architecture` / Core constraints  
- Workforce: [[../workforce/WORKFORCE|WORKFORCE]]  
- Orchestrator: [[../agents/ORCHESTRATOR|ORCHESTRATOR]]  
- Agent Factory: [[../agent_factory/AGENT_FACTORY|AGENT_FACTORY]]  
- Execution Engine: [[../execution/EXECUTION_ENGINE|EXECUTION_ENGINE]]  
- Knowledge base: `knowledge/` (this wiki)

---

## What ADOS OS is / is not

| Is | Is not |
|----|--------|
| Coordination kernel for AI & platform services | A god module owning business logic |
| Registry + event + schedule + memory fabric | A replacement for CRM/ERP domain apps |
| Host for Orchestrator & Execution Engine | Tightly bound to one LLM or IDE vendor |
| Boundary for providers & external tools | Business rules inside adapters |

---

## Main responsibilities

### AI orchestration

- Host and start the **ADOS Orchestrator**.  
- Ensure understand → route → review before implementation.  
- Coordinate workforce divisions without merging their ownership.

Detail: [[../agents/ORCHESTRATOR|ORCHESTRATOR]] · [[../workforce/TASK_ROUTING|TASK_ROUTING]]

### Agent lifecycle

- Register, activate, pause, and stop agents via Factory + Registry hooks.  
- Enforce Agent Contract at activation.  
- Emit lifecycle events (`AgentActivated`, `AgentStopped`).

Detail: [[../agent_factory/AGENT_LIFECYCLE|AGENT_LIFECYCLE]] · [[KERNEL]]

### Task scheduling

- Priority queues, dependency-aware waves, retries, timeouts.  
- Feed Parallel Execution from the Execution Engine.

Detail: [[TASK_SCHEDULER]] · [[../execution/PARALLEL_EXECUTION|PARALLEL_EXECUTION]]

### Knowledge routing

- Route queries and updates to the correct knowledge surfaces (specs, registries, Obsidian pages).  
- Never invent ownership; Knowledge Division remains steward.

Detail: [[../workforce/WORKFORCE|WORKFORCE]] · [[MEMORY_MANAGER]]

### Memory

- Short-term, working, long-term, enterprise, project, and agent memory scopes.  
- Separate volatile runtime state from durable knowledge.

Detail: [[MEMORY_MANAGER]]

### Workflow execution

- Register workflow definitions; run patterns (New Feature, Bug Fix, …).  
- Bind workflows to Execution Engine stages and states.

Detail: [[../execution/EXECUTION_ENGINE|EXECUTION_ENGINE]] · [[../workforce/WORKFLOW_PATTERNS|WORKFLOW_PATTERNS]]

### Event processing

- Enterprise event bus for task, review, deploy, knowledge, and agent events.  
- Loose coupling between producers and consumers.

Detail: [[EVENT_BUS]]

### Security context

- AuthN/Z context for every task and agent invocation.  
- Propagate tenant, role, and permission boundaries; honor Security Blocks.

### User context

- Active user/owner/session intent for routing and UI surfaces.  
- Preserve who requested what (audit + Package-ID linkage).

### Enterprise coordination

- Align CEO/Board/Orchestrator/divisions through OS services—not through ad-hoc chats.  
- Service Registry as the map of what is alive and healthy.

Detail: [[SERVICE_REGISTRY]] · [[../workforce/ORGANIZATION_CHART|ORGANIZATION_CHART]]

---

## Logical stack

```text
┌─────────────────────────────────────────────┐
│  Modules (CRM, ERP, Marketplace, …)         │  ← [[MODULE_SYSTEM]]
├─────────────────────────────────────────────┤
│  Execution Engine · Workflows · Orchestrator│
├─────────────────────────────────────────────┤
│  Agent Factory · Knowledge routing · Memory │
├─────────────────────────────────────────────┤
│  Task Scheduler · Event Bus · Service Registry │
├─────────────────────────────────────────────┤
│  ADOS Kernel                                │  ← [[KERNEL]]
├─────────────────────────────────────────────┤
│  Providers (LLM, storage, messaging, …)     │
└─────────────────────────────────────────────┘
```

Startup: [[STARTUP_SEQUENCE]].

---

## Coupling rule (non-negotiable)

External systems (GitHub, Cursor, Claude, OpenAI, Obsidian, Telegram) and future providers attach **only** through provider/adapter boundaries and events/registry entries.

- No business logic in providers.  
- No module imports another module’s internals to “share OS.”  
- OS exposes services; modules consume capabilities by **Service ID**, not by hard dependency on peer apps.

---

## Success criteria

- Every AI capability can be located via Service Registry.  
- Every significant state change can be observed on the Event Bus.  
- Startup is deterministic ([[STARTUP_SEQUENCE]]).  
- Architecture, Factory, Execution, and Knowledge remain independent packages coordinated by OS—not fused into one codebase god-object.

---

## Related pages

[[KERNEL]] · [[SERVICE_REGISTRY]] · [[EVENT_BUS]] · [[TASK_SCHEDULER]] · [[MEMORY_MANAGER]] · [[MODULE_SYSTEM]] · [[STARTUP_SEQUENCE]]
