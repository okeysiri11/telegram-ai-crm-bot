---
title: Port ERP Detail
aliases:
  - Port ERP Detail
tags:
  - diagram
  - architecture
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Port ERP Detail

## Overview
Port ERP domain architecture.

## Architecture
```mermaid
flowchart TB
  F[PortERPApplication] --> CORE[Port Core]
  F --> TR[Tracking]
  F --> TERM[Terminal]
  F --> CUS[Customs]
  F --> LOG[Logistics]
  F --> AI[AI Ops / Twin]
  F --> FIN[Finance]
  F --> ENT[Enterprise]
  F --> BR[Bridges]
```

## Components
- Hub: [[Port ERP]]

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
