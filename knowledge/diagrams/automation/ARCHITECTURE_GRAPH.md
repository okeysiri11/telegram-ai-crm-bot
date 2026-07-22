---
title: Architecture Graph
aliases:
  - Architecture Graph
tags:
  - diagram
  - automation
  - knowledge-1.2
generated: 2026-07-22
sprint: Knowledge 1.2
---
# Architecture Graph

## Overview
Auto-regenerated Mermaid diagram (Architecture Graph) by Documentation Assistant.

## Architecture
```mermaid
flowchart TB
  CORE[Platform Core]
  ECO[Ecosystem]
  KNOW[Knowledge Vault]
    APP_0[__pycache__]
  APP_1[agro_marketplace]
  APP_2[auto_marketplace]
  APP_3[drone_platform]
  APP_4[port_erp]
  KNOW --> CORE
  KNOW --> ECO
    APP_0 -->|bridges| CORE
  APP_1 -->|bridges| CORE
  APP_2 -->|bridges| CORE
  APP_3 -->|bridges| CORE
  APP_4 -->|bridges| CORE
    APP_0 -->|bridges| ECO
  APP_1 -->|bridges| ECO
  APP_2 -->|bridges| ECO
  APP_3 -->|bridges| ECO
  APP_4 -->|bridges| ECO

```

## Components
- Generated from current module/API/agent scan

## Relationships
[[ARCHITECTURE_DASHBOARD]] · [[diagrams/PLATFORM_GRAPH]] · [[build_graph]]

## Responsibilities
Keep graphs synchronized with repository structure.

## Interfaces
`python3 knowledge/tools/build_graph.py`

## REST APIs
API graph reflects discovered prefixes only

## Events
mermaid_regenerated

## Future roadmap
[[ROADMAP]]

## References
[[automation/DOCUMENTATION_ASSISTANT]]

## Related pages
[[INDEX]] · [[DASHBOARD]]
