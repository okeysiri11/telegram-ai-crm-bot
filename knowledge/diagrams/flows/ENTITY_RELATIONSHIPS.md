---
title: Entity Relationships
aliases:
  - Entity Relationships
tags:
  - diagram
  - flow
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Entity Relationships

## Overview
Entity Relationships Mermaid diagram for Knowledge 1.1.

## Architecture
```mermaid
erDiagram
  PLATFORM ||--o{ APPLICATION : bridges
  ECOSYSTEM ||--o{ APPLICATION : bridges
  APPLICATION ||--o{ MODULE : contains
  APPLICATION ||--o{ AGENT : hosts
  SPRINT ||--o{ APPLICATION : delivers
  AGENT }o--|| ORCHESTRATOR : scheduled_by
  AGENT }o--o| MEMORY : uses
```

## Components
- Related: [[diagrams/DATA_FLOW]] · [[AI Agents]]

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
