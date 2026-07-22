---
title: Legal Platform Detail
aliases:
  - Legal Platform Detail
tags:
  - diagram
  - architecture
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Legal Platform Detail

## Overview
Legal Platform scaffold architecture.

## Architecture
```mermaid
flowchart TB
  V[src/verticals/legal] --> R[Routing]
  V --> LA[Legal Agent]
  LA --> ORCH[Orchestrator]
  FUTURE[applications/legal_platform] -.-> V
```

## Components
- Hub: [[Legal Platform]]

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
