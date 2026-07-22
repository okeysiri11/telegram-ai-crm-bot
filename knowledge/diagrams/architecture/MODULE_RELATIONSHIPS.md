---
title: Module Relationships
aliases:
  - Module Relationships
tags:
  - diagram
  - architecture
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Module Relationships

## Overview
Relationships between all major modules.

## Architecture
```mermaid
flowchart TB
  CORE[Platform Core]
  ECO[Ecosystem]
  AGRO[Agro]
  PORT[Port]
  AUTO[Auto]
  DRONE[Drone]
  CRM[CRM]
  LEGAL[Legal]
  KNOW[Knowledge Vault]
  AGRO --> ECO
  PORT --> ECO
  AUTO --> ECO
  DRONE --> ECO
  AGRO --> CORE
  PORT --> CORE
  AUTO --> CORE
  DRONE --> CORE
  CRM --> AUTO
  CRM --> AGRO
  LEGAL --> CORE
  KNOW -.-> CORE
  KNOW -.-> ECO
  KNOW -.-> AGRO
  KNOW -.-> PORT
  KNOW -.-> AUTO
  KNOW -.-> DRONE
```

## Components
- See [[diagrams/APPLICATION_GRAPH]]

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
