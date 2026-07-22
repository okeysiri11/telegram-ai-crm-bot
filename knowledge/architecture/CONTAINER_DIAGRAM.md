---
title: Container Diagram
aliases:
  - Container Diagram
tags:
  - architecture
  - diagram
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# Container Diagram

## Overview
Container-level view of runtime vs knowledge infrastructure.

## Architecture
Auto-generated architecture visualization (Knowledge 2.2).

## Components
```mermaid
flowchart LR
  WEB[API Gateway aiohttp]
  CORE[Platform Services]
  ECO[Ecosystem Services]
  APPS[Application Containers]
  DB[(Database)]
  KNOW[Knowledge Vault]
  WEB --> CORE
  WEB --> ECO
  WEB --> APPS
  CORE --> DB
  APPS --> DB
  KNOW -.-> WEB

```

Also see PlantUML twin when present.

## Relationships
[[architecture/README]] · [[ARCHITECTURE_DASHBOARD]] · [[diagrams/automation/README]]

## Responsibilities
Provide enterprise development infrastructure without changing runtime logic.

## Interfaces
Markdown + generators under `knowledge/tools/`.

## REST APIs
N/A — documentation/infrastructure only.

## Events
generated_by_enterprise_infra

## Future roadmap
[[ROADMAP]]

## References
[[automation/ENTERPRISE_INFRASTRUCTURE]]

## Related pages
[[INDEX]] · [[PROJECT_STATUS]] · [[EXECUTIVE_DASHBOARD]]
