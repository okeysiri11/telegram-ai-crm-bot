# Memory Engine


---
[[INDEX]] · [[PLATFORM_CORE]] · [[ARCHITECTURE]] · [[API_REFERENCE]]


## Overview
`platform_memory` (version **2.2.0**) provides session, long-term, and semantic memory for agents and applications. Delivered across Sprints **2.1–2.2**.

## Architecture
Memory services expose remember/recall APIs used by orchestrator, assistants, and application bridges. Semantic memory enables similarity retrieval over stored content. Details: `docs/architecture/PLATFORM_MEMORY.md`.

## Components
- Session memory
- Persistent / long-term memory
- Semantic memory (embeddings / similarity)
- Bridge adapters in applications (`integrations/platform_bridge.py`)

## Relationships
- Consumed by [[AI_AGENTS]] and Ecosystem unified assistant.
- Complements [[KNOWLEDGE_GRAPH]] (structured ecosystem knowledge vs episodic/session memory).
- Part of [[PLATFORM_CORE]].

## APIs
Python service APIs via `platform_memory` (e.g. `remember_session_memory`). HTTP exposure is through Platform `/api/v1` where configured; apps typically call through bridges.

## Future roadmap
Cross-tenant memory isolation hardening and richer semantic indexes ([[ROADMAP]]).

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
