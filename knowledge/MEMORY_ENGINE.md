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
