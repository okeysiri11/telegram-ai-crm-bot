---
title: Memory Engine Detail
aliases:
  - Memory Engine Detail
tags:
  - diagram
  - architecture
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Memory Engine Detail

## Overview
Memory engine architecture diagram.

## Architecture
```mermaid
flowchart TB
  APP[App Bridge] --> SM[Session Memory]
  APP --> LM[Long-term Memory]
  APP --> SEM[Semantic Memory]
  SEM --> IDX[Similarity Index]
  SM --> ORCH[Orchestrator]
  LM --> ASST[Assistants]
```

## Components
- Canonical: [[Memory Engine]] / [[MEMORY_ENGINE]]

## Relationships
[[ARCHITECTURE_DASHBOARD]] · [[ARCHITECTURE]] · [[INDEX]] · [[Platform Core]] · [[AI Agents]]

## Responsibilities
Visualize structure for Obsidian and engineering onboarding.

## Interfaces
Mermaid diagram rendered in Obsidian.

## REST APIs
See [[registries/API_REGISTRY]] when applicable.

## Events
N/A (documentation diagram).

## Future roadmap
Keep diagrams aligned after each sprint via [[automation/DOCUMENTATION_AUTOMATION]].

## References
`docs/architecture.md` and app docs.

## Related pages
[[DASHBOARD]] · [[diagrams/PLATFORM_GRAPH]] · [[diagrams/APPLICATION_GRAPH]]
