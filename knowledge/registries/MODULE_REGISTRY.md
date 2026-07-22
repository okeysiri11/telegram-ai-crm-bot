---
title: Module Registry
aliases:
  - Module Registry
tags:
  - registry
  - modules
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---
# Module Registry

> Auto-generated 2026-07-22 · [[INDEX]]

## Overview
Inventory of Platform Core packages, Ecosystem modules, and Drone Platform modules.

## Architecture
Modules are package-level units. Applications compose modules behind facades.

## Components
### Platform Core
`platform_memory`, `platform_orchestrator`, `platform_agents`, `platform_workflow`, `platform_tools`, `platform_plugin_sdk`, `platform_plugins`, `platform_reasoning`, `platform_planning`, `platform_decision`, `platform_learning`, `platform_collaboration`, `platform_security`, `platform_observability`, `platform_reliability`, `platform_configuration`, `platform_validation`, `platform_api`, `platform_sdk`, `platform_management`

### Ecosystem
`identity`, `workspace`, `navigation`, `organizations`, `tenants`, `profiles`, `permissions`, `services`, `ai`, `communication`, `assistant`, `workforce`, `optimization`, `governance`

### Drone Platform
`registry`, `projects`, `engineering`, `firmware`, `missions`, `telemetry`, `inventory`, `warehouse`, `manufacturing`, `simulation`, `ai`, `documentation`, `integrations`, `analytics`, `shared`, `api`, `models`

**Counts:** platform=20, ecosystem=14, drone=17

## Relationships
[[Platform Core]] · [[registries/COMPONENT_REGISTRY]] · [[glossary/COMPONENTS]]

## Responsibilities
Name and track modules; do not duplicate business logic in knowledge tooling.

## Interfaces
Registry JSON `modules` map.

## REST APIs
Modules expose APIs via their owning layer — [[registries/API_REGISTRY]].

## Events
Module load / plugin init on API startup.

## Future roadmap
Add Legal modules when productized.

## References
`platform_manifest.json`, `ecosystem/manifest.json`, drone `manifest.json`.

## Related pages
[[Plugin SDK]] · [[Memory Engine]] · [[Workflow Engine]] · [[AI Agents]]
