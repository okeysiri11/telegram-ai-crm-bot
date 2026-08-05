---
title: ADOS Service Registry
aliases:
  - Service Registry
tags:
  - ados-os
  - registry
status: foundation
---

# ADOS Service Registry

## Purpose

Describe how **every internal service** registers itself with ADOS OS so Orchestrator, modules, and providers discover capabilities **by identity**, not by hard-wired imports.

OS: [[ADOS_OS]] · Kernel: [[KERNEL]] · Events: [[EVENT_BUS]]

---

## Registration principle

```text
Service starts → declares metadata → Kernel validates deps → Registry accepts → Health monitored
```

No undeclared service may receive scheduled tasks or emit privileged events.

---

## Registration record

| Field | Description |
|-------|-------------|
| **Service ID** | Stable unique id (`ados.orchestrator`, `ados.execution`, `module.crm`, `provider.openai`) |
| **Version** | Semver of the service implementation |
| **Capabilities** | Declared verbs/surfaces (`route_task`, `run_workflow`, `chat.complete`, `crm.deals.list`) |
| **Dependencies** | Service IDs that must be healthy before this service is Ready |
| **Health Status** | `starting` \| `healthy` \| `degraded` \| `unhealthy` \| `stopped` |
| **Owner** | Division / Lead / team accountable (e.g. Knowledge Lead, Engineering Manager) |

Optional extensions: edition flags, security classification, event types produced/consumed.

---

## Example records

```text
Service ID:     ados.orchestrator
Version:        1.0.0
Capabilities:   understand, route, gate_review, merge_readiness
Dependencies:   ados.event_bus, ados.task_scheduler, ados.memory
Health Status:  healthy
Owner:          ADOS Orchestrator / CEO coordination mandate

Service ID:     module.crm
Version:        …
Capabilities:   crm.* domain APIs
Dependencies:   ados.kernel, ados.event_bus
Health Status:  healthy
Owner:          Business Division / Product Manager

Service ID:     provider.openai
Version:        …
Capabilities:   llm.chat, llm.embed
Dependencies:   (none internal; external network)
Health Status:  healthy | degraded
Owner:          Infrastructure Division
```

---

## Lifecycle of a registration

| Step | Action |
|------|--------|
| 1 | Module/provider calls register with full record |
| 2 | Kernel checks Dependency graph (no missing critical deps) |
| 3 | Registry stores Version; duplicate ID requires compatible upgrade rules |
| 4 | Health probes begin |
| 5 | On `unhealthy`, dependents may degrade; Orchestrator stops routing new work to it |
| 6 | On stop, emit service-stopped (and `AgentStopped` if agent-backed) |

---

## Discovery rules

1. Consumers resolve **Service ID + Capability**, never peer filesystem paths.  
2. Version negotiation: prefer declared compatible range; fail closed if incompatible.  
3. Owner is required for escalation ([[../workforce/ESCALATION_MODEL|ESCALATION_MODEL]]).  
4. Capability names are additive; renames need deprecation via Knowledge + Registry.

---

## Health Status semantics

| Status | Scheduler / Orchestrator behavior |
|--------|-----------------------------------|
| `starting` | Do not assign new tasks |
| `healthy` | Eligible |
| `degraded` | Eligible with caution; prefer alternatives if capability duplicated |
| `unhealthy` | Not eligible; alert Owner |
| `stopped` | Unregister or retain tombstone per policy |

---

## Anti-patterns

- Hidden services used only via direct import.  
- Capabilities that embed another module’s domain (`provider.*` doing CRM rules).  
- Missing Owner.  
- Circular Dependencies without explicit break (events instead of sync deps).

---

## Related

[[MODULE_SYSTEM]] · [[STARTUP_SEQUENCE]] · [[../agent_factory/AGENT_REGISTRY|AGENT_REGISTRY]]
