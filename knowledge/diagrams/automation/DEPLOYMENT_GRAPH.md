---
title: Deployment Graph Automated
aliases:
  - Deployment Graph Automated
tags:
  - diagram
  - automation
  - knowledge-1.2
generated: 2026-07-22
sprint: Knowledge 1.2
---
# Deployment Graph Automated

## Overview
Auto-regenerated Mermaid diagram (Deployment Graph Automated) by Documentation Assistant.

## Architecture
```mermaid
flowchart LR
  CFG[Config] --> API[api/server.py]
  API --> HEALTH[Health]
  API --> ROUTES[Routers]
  ROUTES --> V1[/api/v1]
  ROUTES --> ECO[/api/ecosystem/v1]
  ROUTES --> APPS[/api/agro|port|auto|drone/v1]

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
