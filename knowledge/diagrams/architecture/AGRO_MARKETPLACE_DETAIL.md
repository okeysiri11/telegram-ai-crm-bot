---
title: Agro Marketplace Detail
aliases:
  - Agro Marketplace Detail
tags:
  - diagram
  - architecture
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Agro Marketplace Detail

## Overview
Agro Marketplace domain architecture.

## Architecture
```mermaid
flowchart TB
  F[AgroFacade] --> CAT[Catalog/Harvest]
  F --> CRM[CRM/Trading]
  F --> EXP[Export/Logistics]
  F --> AI[Agro AI]
  F --> AN[Analytics]
  F --> POR[Portal/Partner]
  F --> BR[Bridges]
```

## Components
- Hub: [[Agro Marketplace]]

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
