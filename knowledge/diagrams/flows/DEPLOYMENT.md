---
title: Deployment Flow
aliases:
  - Deployment Flow
tags:
  - diagram
  - flow
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Deployment Flow

## Overview
Deployment Flow Mermaid diagram for Knowledge 1.1.

## Architecture
```mermaid
flowchart TB
  CFG[Configuration / Flags] --> APP[API Process]
  APP --> HEALTH[/health /liveness /readiness]
  APP --> METRICS[/metrics]
  APP --> PLUG[Plugin Manager]
  APP --> ROUTES[Mounted Routers]
  ROUTES --> CORE[/api/v1]
  ROUTES --> ECO[/api/ecosystem/v1]
  ROUTES --> APPS[/api/agro|port|auto|drone/v1]
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
