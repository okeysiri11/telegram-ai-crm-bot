# Application Graph

---
[[INDEX]] · [[ARCHITECTURE]] · [[diagrams/PLATFORM_GRAPH]] · [[diagrams/AGENT_GRAPH]] · [[diagrams/APPLICATION_GRAPH]] · [[diagrams/DATA_FLOW]]


## Overview
Vertical applications and cross-cutting CRM/Legal capabilities relative to Core and Ecosystem.

## Architecture
```mermaid
flowchart TB
  CORE[[Platform Core]]
  ECO[[Ecosystem]]
  AGRO[Agro Marketplace]
  PORT[Port ERP]
  AUTO[Auto Marketplace]
  DRONE[Drone Platform]
  CRM[CRM capability]
  LEGAL[Legal scaffold]
  AGRO --> ECO
  AGRO --> CORE
  PORT --> ECO
  PORT --> CORE
  AUTO --> ECO
  AUTO --> CORE
  DRONE --> ECO
  DRONE --> CORE
  CRM -.-> AUTO
  CRM -.-> AGRO
  LEGAL -.-> CORE
  AUTO -.->|optional bridges| AGRO
  AUTO -.->|optional bridges| PORT
```

## Components
Pages: [[applications/AGRO_MARKETPLACE]], [[applications/PORT_ERP]], [[applications/AUTO_MARKETPLACE]], [[applications/DRONE_PLATFORM]], [[applications/CRM]], [[applications/LEGAL_PLATFORM]].

## Relationships
Optional Auto→Agro/Port bridges are outbound only. Drone is isolated besides Core/Ecosystem bridges.

## APIs
Per-app prefixes in [[API_REFERENCE]].

## Future roadmap
Promote Legal to full application node; register all apps in Ecosystem manifest ([[ROADMAP]]).
