---
title: Database ER Diagram
aliases:
  - Database ER Diagram
tags:
  - architecture
  - diagram
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# Database ER Diagram

## Overview
Logical ER-style diagram for platform entities (documentation model).

## Architecture
Auto-generated architecture visualization (Knowledge 2.2).

## Components
```mermaid
erDiagram
  PLATFORM ||--o{ APPLICATION : hosts
  APPLICATION ||--o{ MODULE : contains
  APPLICATION ||--o{ AGENT : documents
  SPRINT ||--o{ RELEASE : produces

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
