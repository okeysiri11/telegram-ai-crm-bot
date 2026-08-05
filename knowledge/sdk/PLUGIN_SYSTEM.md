---
title: ADOS Plugin System
aliases:
  - Plugin System
tags:
  - sdk
  - plugins
status: foundation
---

# ADOS Plugin System

## Purpose

Describe the **plugin architecture**—typed extension packs that register with ADOS through the SDK and Plugin Manager, not through Core forks.

SDK: [[SDK_OVERVIEW]] · Manifest: [[PLUGIN_MANIFEST]] · OS modules: [[../ados_os/MODULE_SYSTEM|MODULE_SYSTEM]]

---

## Architecture

```text
Plugin (typed)
  → Manifest + Permissions + Entry Points
  → SDK APIs / Hooks
  → Plugin Manager
  → Service Registry + Runtime + OS
```

A **module** (CRM, ERP) may be delivered *as* a Business Plugin or composed of several plugins. UPP adapters are typically **Provider Plugins**.

---

## Plugin types

| Type | Purpose | Typical SDK use |
|------|---------|-----------------|
| **Business Plugin** | Domain capabilities (vertical packs, CRM extensions) | Task, Workflow, Knowledge, Memory |
| **Provider Plugin** | External system adapters (LLM, VCS, messaging) | Provider API, Event Bus; **no domain rules** |
| **AI Plugin** | Agents, skills, prompt packs, tool bundles | Runtime, Memory, Knowledge; Factory-aligned |
| **UI Plugin** | Surfaces, layouts, operator consoles | Event Bus, Task (read), declared UI entry points |
| **Workflow Plugin** | Workflow definitions & stage customizations | Workflow API, Hooks (task/deploy) |
| **Analytics Plugin** | Metrics, dashboards, telemetry sinks | Event Bus (consume), Knowledge (write reports) |
| **Automation Plugin** | Triggers, scheduled automations, bots | Task, Workflow, Runtime, Hooks |
| **Security Plugin** | Policy packs, scanners, authz extensions | Security API; elevated review to Enable |
| **Connector Plugin** | Thin bridges (webhooks, ETL-lite, sync) | Provider + Event Bus; prefer UPP where possible |

---

## Isolation rules

1. Plugins communicate via **SDK APIs**, **hooks**, and **events**—not peer internals.  
2. Business Plugins must not import Provider SDK vendor types.  
3. Provider Plugins must not call Business domain services except via normalized OS/module APIs if explicitly permitted.  
4. UI Plugins cannot Enable without declared entry points and Read-scoped defaults.  
5. Security Plugins require Security Lead (or policy) before Enable in production.

---

## Relationship to Agent Factory

AI Plugins that ship agents must still pass Factory Contract/Lifecycle; the plugin is the **distribution unit**, Factory is the **agent quality gate**.

---

## Related

[[PLUGIN_LIFECYCLE]] · [[PERMISSION_MODEL]] · [[../providers/PROVIDER_INTERFACE|PROVIDER_INTERFACE]] · [[../agent_factory/FACTORY_RULES|FACTORY_RULES]]
