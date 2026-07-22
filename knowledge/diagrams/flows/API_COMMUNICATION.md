---
title: API Communication
aliases:
  - API Communication
tags:
  - diagram
  - flow
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# API Communication

## Overview
API Communication Mermaid diagram for Knowledge 1.1.

## Architecture
```mermaid
sequenceDiagram
  participant C as Client
  participant GW as API Gateway
  participant APP as App API
  participant BR as Bridge
  participant CORE as Platform Core
  C->>GW: REST /api/<app>/v1
  GW->>APP: route
  APP->>BR: auth/memory/workflow
  BR->>CORE: optional call
  CORE-->>BR: result/stub
  APP-->>C: JSON
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
