---
title: ADOS SDK API
aliases:
  - SDK API
tags:
  - sdk
  - api
status: foundation
---

# ADOS SDK API

## Purpose

Describe the **available SDK interfaces**—the only supported programmatic surfaces for plugins and extension authors.

SDK: [[SDK_OVERVIEW]] · Permissions: [[PERMISSION_MODEL]] · Hooks: [[HOOK_SYSTEM]]

---

## Design principles

1. **Stable & versioned** — breaking changes only in major SDK versions.  
2. **Capability-oriented** — prefer verbs over exposing internal classes.  
3. **Permission-gated** — every call checks grant.  
4. **Normalized** — Provider API returns UPP-normalized shapes.  
5. **No Core leakage** — internals remain private.

---

## Interfaces (examples)

### Knowledge API

- Read/write Knowledge Memory surfaces; resolve docs/nodes by id.  
- Trigger index hints; emit knowledge-update hooks.  
- Aligns with [[../memory/KNOWLEDGE_GRAPH|KNOWLEDGE_GRAPH]] / [[../memory/KNOWLEDGE_INDEX|KNOWLEDGE_INDEX]].

### Memory API

- Working / agent / project memory via Memory Engine.  
- Retrieval and gated durable writes.  
- See [[../memory/MEMORY_ENGINE|MEMORY_ENGINE]].

### Provider API

- `execute` / `stream` by **capability** (not vendor).  
- Health and failover remain inside UPP; SDK is the caller façade.  
- See [[../providers/PROVIDER_ROUTER|PROVIDER_ROUTER]].

### Workflow API

- Register/list workflow definitions; start/signal workflow instances.  
- Respect Execution Engine stages—plugins do not invent skip-gate APIs.  
- See [[../execution/EXECUTION_ENGINE|EXECUTION_ENGINE]].

### Task API

- Create/assign/query Tasks and Execution Units (within permission).  
- Handoff helpers aligned with Handoff Protocol.  
- Orchestrator remains authority for enterprise routing policy.

### Runtime API

- Session info, cancel/retry requests, queue class hints, execution log append (scoped).  
- Heartbeat helpers for long AI Plugins.  
- See [[../runtime/AI_RUNTIME|AI_RUNTIME]].

### Security API

- Evaluate permission scopes; request elevation (does not auto-grant).  
- Audit helpers; secret **handles** resolve only with Secret Access.  
- Aligns with [[../providers/PROVIDER_SECURITY|PROVIDER_SECURITY]] patterns.

### Event Bus API

- Publish/subscribe to allowed event types.  
- Idempotent handlers; no domain “command bus” abuse.  
- See [[../ados_os/EVENT_BUS|EVENT_BUS]].

---

## Additional recommended surfaces

| API | Role |
|-----|------|
| **Hook API** | Register callbacks for [[HOOK_SYSTEM]] |
| **Plugin Context API** | Manifest identity, config (non-secret), health report |
| **UI Extension API** | Declare slots for UI Plugins (host-defined) |

---

## Usage rule for agents

Factory-built agents that need platform access should call **SDK APIs** (or tools backed by them)—not ad-hoc filesystem or Core imports—so they remain portable plugins/skills.

---

## Related

[[PLUGIN_SYSTEM]] · [[PERMISSION_MODEL]] · [[../runtime/EXECUTION_LOG|EXECUTION_LOG]]
