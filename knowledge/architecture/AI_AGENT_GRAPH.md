---
title: AI Agent Graph
aliases:
  - AI Agent Graph
tags:
  - architecture
  - diagram
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# AI Agent Graph

## Overview
Documented AI agent topology.

## Architecture
Auto-generated architecture visualization (Knowledge 2.2).

## Components
```mermaid
flowchart LR
  ORCH[Orchestrator]
    ORCH --> A0[Developer AI]
  ORCH --> A1[CRM AI]
  ORCH --> A2[Marketplace AI]
  ORCH --> A3[Owner AI]
  ORCH --> A4[Agro AI]
  ORCH --> A5[Architect AI]
  ORCH --> A6[Manager AI]
  ORCH --> A7[Port AI]
  ORCH --> A8[Legal AI]
  ORCH --> A9[Finance AI]
  ORCH --> A10[Drone Engineer AI]
  ORCH --> A11[QA AI]

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
