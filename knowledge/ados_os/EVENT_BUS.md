---
title: ADOS Event Bus
aliases:
  - Event Bus
  - Enterprise Events
tags:
  - ados-os
  - events
status: foundation
---

# ADOS Event Bus

## Purpose

Describe the **enterprise event architecture** that lets ADOS OS components communicate **asynchronously** without hard coupling.

OS: [[ADOS_OS]] · Kernel: [[KERNEL]] · Execution: [[../execution/EXECUTION_ENGINE|EXECUTION_ENGINE]]

---

## Design principles

1. **Facts, not commands** — events state what happened; handlers decide reaction.  
2. **Package-ID correlation** — every work-related event carries the execution package id.  
3. **No business logic on the bus** — handlers live in services/modules.  
4. **Ordered where required** — per Package-ID causal order for critical chains.  
5. **Auditability** — security-relevant events retained per policy.

---

## Event envelope

```text
EventType:     <name>
EventID:       <uuid>
Timestamp:     <iso8601>
Package-ID:    <id | null>
Service ID:    <producer>
Actor:         <user | agent | system>
Payload:       <typed fields>
Security ctx:  <tenant/roles as allowed>
```

---

## Core event catalog (examples)

| Event | When | Typical consumers |
|-------|------|-------------------|
| **TaskCreated** | Decomposer/Orchestrator mints a Task | Scheduler, Knowledge audit |
| **TaskAssigned** | Team/agent ownership set | Agent runtime, UI, metrics |
| **ReviewRequested** | Deliverable entered Review | Architect, Security, QA, Docs |
| **ReviewApproved** | Gate Approval | Scheduler (unblock), Orchestrator |
| **DeploymentStarted** | Enter Deploying | Ops, monitoring, Customer comms |
| **DeploymentCompleted** | Deploy success (or terminal fail subtype) | Feedback, Learning, docs freeze |
| **KnowledgeUpdated** | Specs/registries changed | Search index, agents, Obsidian sync adapter |
| **AgentActivated** | Agent lifecycle Activate | Scheduler eligibility, Workforce views |
| **AgentStopped** | Pause/Retire/Stop | Scheduler, audit |

### Extended events (recommended)

`TaskBlocked`, `TaskUnblocked`, `ReviewRejected`, `ReworkRequested`, `QAPassed`, `QAFailed`, `WorkflowStarted`, `WorkflowCompleted`, `ServiceHealthChanged`, `MemoryCompacted`, `LearningArchived`.

---

## Topology

```text
Producers (Orchestrator, Execution, Modules, Agents, Providers*)
        ↓
   Event Bus
        ↓
Consumers (Scheduler, Registry, Memory, Modules, Audit, External adapters)
```

\* Providers emit only infrastructure facts (e.g. model call completed)—never domain decisions.

---

## Delivery semantics

| Mode | Use |
|------|-----|
| **At-least-once** | Default for Task/Review/Deploy |
| **Idempotent handlers** | Required (EventID dedupe) |
| **Dead-letter** | After retry exhaustion → Owner alert |
| **Sync call-out** | Forbidden as substitute for events between modules |

Retries/timeouts align with [[TASK_SCHEDULER]].

---

## Security context on events

- Strip or redact secrets from Payload.  
- Propagate tenant and permission scope for authorization of consumers.  
- Security **Block** outcomes may emit `ReviewRejected` / custom `SecurityBlocked` with high severity.

---

## Coupling rule

Modules subscribe to **event types**, not to each other’s classes.  
GitHub/Cursor/Telegram/Obsidian adapters are **consumers/producers at the edge**, translating external webhooks ↔ ADOS events.

---

## Related

[[SERVICE_REGISTRY]] · [[TASK_SCHEDULER]] · [[../execution/EXECUTION_STATES|EXECUTION_STATES]] · [[../workforce/COMMUNICATION_PROTOCOL|COMMUNICATION_PROTOCOL]]
