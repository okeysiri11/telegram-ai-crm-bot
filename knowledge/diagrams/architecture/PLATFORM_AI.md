---
title: Platform AI
aliases:
  - Platform AI Detail
tags:
  - diagram
  - architecture
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Platform AI

## Overview
Platform AI cognitive and agentic stack.

## Architecture
```mermaid
flowchart LR
  R[Reasoning] --> P[Planning]
  P --> D[Decision]
  D --> L[Learning]
  L --> C[Collaboration]
  C --> O[Orchestrator]
  O --> A[Agents]
  A --> M[Memory]
  A --> T[Tools]
```

## Components
- [[AI Agents]] · [[Memory Engine]] · [[Workflow Engine]] · [[Plugin SDK]]

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
