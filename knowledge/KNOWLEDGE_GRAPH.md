# Knowledge Graph


---
[[INDEX]] · [[PLATFORM_CORE]] · [[ARCHITECTURE]] · [[API_REFERENCE]]


## Overview
Global knowledge graph capabilities live in the **AI Ecosystem** (`ecosystem/assistant/knowledge_graph/`, layer `global_knowledge` **1.0**), not as a Platform Core package. Introduced with Ecosystem Sprint **7.3** (unified assistant).

## Architecture
Structured entities and relations support the unified assistant and workforce layers. Application knowledge bases (e.g. Auto vehicle knowledge modules) remain app-local and may sync via bridges later.

## Components
- Ecosystem global knowledge module
- Unified assistant integration
- Obsidian knowledge vault (this `knowledge/` wiki) for human navigation
- App-local knowledge packages (e.g. `applications/auto_marketplace/knowledge/`)

## Relationships
- Depends on Ecosystem identity/workspace context.
- Used by [[AI_AGENTS]] executive/workforce flows.
- Distinct from [[MEMORY_ENGINE]] (graph vs memory stores).

## APIs
Ecosystem `/api/ecosystem/v1` assistant/knowledge routes (see `docs/UNIFIED_ASSISTANT.md`, `docs/ECOSYSTEM.md`).

## Future roadmap
Federate Agro/Port/Auto/Drone domain graphs into Ecosystem global knowledge ([[ROADMAP]]).

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
