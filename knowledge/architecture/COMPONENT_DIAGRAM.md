---
title: Component Diagram
aliases:
  - Component Diagram
tags:
  - architecture
  - diagram
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# Component Diagram

## Overview
Component interactions for API routing and knowledge tooling.

## Architecture
Auto-generated architecture visualization (Knowledge 2.2).

## Components
```mermaid
flowchart TB
  API[api/server.py] --> REG[App Routers]
  REG --> BR[Bridges]
  BR --> MEM[Memory]
  BR --> ORCH[Orchestrator]
  BR --> WF[Workflow]
  KNOW[Knowledge Tools] --> MD[Markdown Reports]

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
