---
title: Auto Marketplace Detail
aliases:
  - Auto Marketplace Detail
tags:
  - diagram
  - architecture
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Auto Marketplace Detail

## Overview
Auto Marketplace domain architecture.

## Architecture
```mermaid
flowchart TB
  F[Facade] --> CAT[Catalog/VIN]
  F --> CRM[CRM/AI Sales]
  F --> MKT[Marketplace]
  F --> TX[Transactions]
  F --> SVC[Service]
  F --> LOG[Logistics]
  F --> FLT[Fleet]
  F --> ENT[Enterprise]
  F --> BR[Bridges]
```

## Components
- Hub: [[Auto Marketplace]]

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
