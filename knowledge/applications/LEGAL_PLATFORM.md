# Legal Platform

---
[[INDEX]] · [[ARCHITECTURE]] · [[diagrams/APPLICATION_GRAPH]] · [[API_REFERENCE]]


## Overview
Legal is currently a **scaffold vertical** (`src/verticals/legal/`) plus Legal Agent hooks in the orchestrator — **not** yet a first-class `applications/legal_platform` package. Documented here for navigation and roadmap alignment (`docs/VERTICALS.md`).

## Architecture
Vertical routing pattern shares the Telegram/platform request lifecycle with realty/logistics scaffolds. Intended future shape mirrors other apps: package under `applications/`, bridges to Core/Ecosystem, versioned `/api/legal/v1`.

## Components (current)
- Legal vertical scaffold
- Legal Agent (orchestrator registry)
- Shared routing / roles documentation

## Relationships
- Depends on [[PLATFORM_CORE]] agent/orchestrator stack
- Adjacent to [[applications/CRM]] for matter/client linkage
- Future peer of [[applications/AUTO_MARKETPLACE]] et al.

## APIs
No dedicated `/api/legal/v1` application API yet. Platform/orchestrator APIs apply for agent tasks.

## Future roadmap
Productize as `applications/legal_platform` with contracts, compliance workflows, and Ecosystem governance integration ([[ROADMAP]]).

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
