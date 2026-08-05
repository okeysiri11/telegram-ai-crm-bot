---
title: ADOS Enterprise AI Runtime
aliases:
  - AI Runtime
  - Enterprise AI Runtime
tags:
  - runtime
  - agents
  - execution
status: foundation
---

# ADOS Enterprise AI Runtime

## Purpose

The **ADOS Enterprise AI Runtime** is the layer responsible for **executing, coordinating, monitoring, and supervising every AI agent** inside ADOS.

It turns Orchestrator packages and scheduled work into live agent sessions—with queues, resources, timeouts, cancellation, retries, recovery, and execution history—while **ADOS OS** remains the operating layer (boot, services, events, memory fabric, modules).

This package is **documentation only**. Do **not** modify existing application code.

Related:

- ADOS OS: [[../ados_os/ADOS_OS|ADOS_OS]]  
- Orchestrator: [[../agents/ORCHESTRATOR|ORCHESTRATOR]]  
- Execution Engine (enterprise stages): [[../execution/EXECUTION_ENGINE|EXECUTION_ENGINE]]  
- UPP: [[../providers/UNIVERSAL_PROVIDER_PLATFORM|UNIVERSAL_PROVIDER_PLATFORM]]  
- Enterprise Memory: [[../memory/ENTERPRISE_MEMORY|ENTERPRISE_MEMORY]]  
- Task Scheduler (OS): [[../ados_os/TASK_SCHEDULER|TASK_SCHEDULER]]

---

## Responsibilities

| Responsibility | Meaning |
|----------------|---------|
| **Execute agents** | Run agent instances against assigned Tasks / Execution Units |
| **Manage sessions** | Workspace, project, conversation, agent, shared, recovery sessions |
| **Allocate resources** | CPU, memory, LLM/provider budget, concurrency slots |
| **Monitor execution** | Heartbeats, duration, cost, health; feed Supervisor |
| **Cancel execution** | Cooperative and forced cancel with cleanup |
| **Retry execution** | Policy-bound retries; no blind logic retries |
| **Recover failures** | Restart sessions, rehydrate from logs/graph, resume or fail cleanly |
| **Maintain execution history** | [[EXECUTION_LOG]] + Decision/Knowledge writes |

---

## Runtime vs OS vs Execution Engine

| Layer | Role |
|-------|------|
| **ADOS OS** | Operating layer: Kernel, Registry, Event Bus, Memory Manager, module plug-in, startup |
| **Execution Engine** | Enterprise pipeline: 14 stages, decomposition, gates, states Requested→Archived |
| **AI Runtime** | Execution layer: *how* agents run now—queues, sessions, resources, supervise, log |

Orchestrator decides **what** and **who**. Runtime decides **when slots run** and **how instances live**. OS keeps the platform **alive and discoverable**.

---

## Logical stack

```text
User / Owner
    ↓
Orchestrator
    ↓
AI Runtime
    ↓
Task Queue · Session Manager · Resource Manager
    ↓
Agent Runtime (+ Supervisor)
    ↓
Provider Platform (UPP)
    ↓
Execution (units complete)
    ↓
Knowledge Graph · Learning Engine
```

---

## Package map

| Document | Role |
|----------|------|
| [[AGENT_RUNTIME]] | Agent instance lifecycle |
| [[TASK_QUEUE]] | Queue classes |
| [[RESOURCE_MANAGER]] | Budgets & limits |
| [[SESSION_MANAGER]] | Session types |
| [[PARALLEL_EXECUTION]] | Parallelism at runtime |
| [[AGENT_COMMUNICATION_PROTOCOL]] | Agent messaging |
| [[SUPERVISOR]] | Detection & intervention |
| [[EXECUTION_LOG]] | History & audit |

---

## Principles

1. Runtime never embeds CRM/ERP business rules.  
2. Providers only via UPP—no vendor SDKs in Agent Runtime core.  
3. Context from Context Engine / Memory—not unbounded chat dumps.  
4. Supervisor can stop runaway agents; Security/Architect gates still bind.  
5. Every run leaves an Execution Log entry correlated to Package-ID.

---

## Related

[[AGENT_RUNTIME]] · [[SUPERVISOR]] · [[../workforce/WORKFORCE|WORKFORCE]]
