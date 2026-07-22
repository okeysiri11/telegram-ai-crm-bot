# Architecture


---
[[INDEX]] · [[ARCHITECTURE]] · [[PLATFORM_CORE]] · [[ROADMAP]] · [[API_REFERENCE]]


## Overview
The repository implements a layered AI operating system: **Platform Core** (certified engines), **AI Ecosystem** (cross-app identity, assistant, governance), and **vertical applications** (Agro, Port, Auto, Drone) that integrate through bridges only.

## Architecture
```
┌─────────────────────────────────────────────────────────┐
│  Applications (Agro · Port · Auto · Drone · CRM/Legal)  │
│  bridges → platform_bridge / ecosystem_bridge           │
├─────────────────────────────────────────────────────────┤
│  AI Ecosystem v1.5.0-alpha  (/api/ecosystem/v1)         │
│  identity · workspace · assistant · workforce · gov     │
├─────────────────────────────────────────────────────────┤
│  Platform Core v3.0.0  (/api/v1 · /management/v1)       │
│  memory · orchestrator · agents · workflow · tools      │
│  reasoning · planning · decision · learning · security  │
└─────────────────────────────────────────────────────────┘
```

Deep baseline: repository `docs/architecture.md`, `docs/ARCHITECTURE_BASELINE.md`.

## Components
- **Platform packages:** `platform_memory`, `platform_orchestrator`, `platform_agents`, `platform_workflow`, `platform_tools`, `platform_plugin_sdk`, cognition engines, ops layers — [[PLATFORM_CORE]]
- **Ecosystem package:** `ecosystem/` — identity, tenants, assistant, knowledge graph, governance
- **Applications:** `applications/*` — see [[diagrams/APPLICATION_GRAPH]]
- **Legacy Telegram CRM gateway:** `/api/*` unversioned paths coexist with frozen `/api/v1`

## Relationships
- Apps **never** modify Core/Ecosystem source; optional imports + stubs.
- [[KNOWLEDGE_GRAPH]] lives in Ecosystem (`global_knowledge`), not Core.
- Agents are registered in Core and may be orchestrated across apps — [[AI_AGENTS]]
- Diagrams: [[diagrams/PLATFORM_GRAPH]] · [[diagrams/DATA_FLOW]]

## APIs
Documented in [[API_REFERENCE]]. Gateway assembly: `api/server.py` mounts management, ecosystem, and application routers.

## Future roadmap
Preserve Core freeze; evolve Ecosystem + apps. See [[ROADMAP]].

## Responsibilities
Document and navigate this concern within the Obsidian living vault (Knowledge 1.1).

## Interfaces
Wiki links, dashboards, and registries. Runtime interfaces described where applicable.

## REST APIs
See [[registries/API_REGISTRY]] and [[API_REFERENCE]] when this page owns HTTP surfaces; otherwise N/A.

## Events
Domain or documentation events as applicable; see related sprint pages.

## References
Repository `docs/`, manifests, [[standards/DOCUMENTATION_STANDARDS]].

## Related pages
[[INDEX]] · [[DASHBOARD]] · [[ROADMAP]] · [[registries/COMPONENT_REGISTRY]]
