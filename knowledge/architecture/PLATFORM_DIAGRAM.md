---
title: Platform Diagram
aliases:
  - Platform Diagram
tags:
  - architecture
  - diagram
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# Platform Diagram

## Overview
High-level platform diagram of Core, Ecosystem, apps, and Knowledge.

## Architecture
Auto-generated architecture visualization (Knowledge 2.2).

## Components
```mermaid
flowchart TB
  subgraph Core[Platform Core]
    platform_agents
  platform_ai
  platform_api
  platform_architecture
  platform_certification
  platform_collaboration
  platform_configuration
  platform_console
  platform_decision
  platform_identity
  platform_integrations
  platform_jobs
  platform_learning
  platform_legacy
  platform_management
  platform_memory
  platform_observability
  platform_operations
  end
  ECO[Ecosystem]
  KNOW[Knowledge 2.0]
    __pycache__[__pycache__]
  agro_marketplace[agro_marketplace]
  auto_marketplace[auto_marketplace]
  drone_platform[drone_platform]
  port_erp[port_erp]
  KNOW --> ECO --> Core
    __pycache__ -->|bridges| ECO
  agro_marketplace -->|bridges| ECO
  auto_marketplace -->|bridges| ECO
  drone_platform -->|bridges| ECO
  port_erp -->|bridges| ECO
    __pycache__ -->|bridges| Core
  agro_marketplace -->|bridges| Core
  auto_marketplace -->|bridges| Core
  drone_platform -->|bridges| Core
  port_erp -->|bridges| Core

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
