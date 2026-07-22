---
title: API Relationship Diagram
aliases:
  - API Relationship Diagram
tags:
  - architecture
  - diagram
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# API Relationship Diagram

## Overview
API relationship diagram across surfaces.

## Architecture
Auto-generated architecture visualization (Knowledge 2.2).

## Components
```mermaid
flowchart TB
  GW[Gateway] --> V1[/api/v1]
  GW --> ECO[/api/ecosystem/v1]
  GW --> AGRO[/api/agro/v1]
  GW --> PORT[/api/port/v1]
  GW --> AUTO[/api/auto/v1]
  GW --> DRONE[/api/drone/v1]

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
