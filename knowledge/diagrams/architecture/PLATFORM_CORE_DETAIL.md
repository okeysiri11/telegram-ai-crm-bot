---
title: Platform Core Detail
aliases:
  - Platform Core Detail
tags:
  - diagram
  - architecture
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Platform Core Detail

## Overview
Certified Platform Core v3.0.0 engine map.

## Architecture
```mermaid
flowchart TB
  API[platform_api / management]
  MEM[platform_memory 2.2]
  ORCH[platform_orchestrator 2.3]
  AG[platform_agents]
  WF[platform_workflow]
  TOOLS[tools / plugins / SDK]
  COG[reasoning planning decision learning collaboration]
  OPS[security obs reliability config validation]
  API --> ORCH
  MEM --> ORCH
  AG --> ORCH
  ORCH --> WF
  WF --> TOOLS
  COG --> ORCH
  OPS --> API
```

## Components
- Packages listed in [[registries/MODULE_REGISTRY]]\n- Hub: [[Platform Core]]

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
