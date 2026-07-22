---
title: Application Graph Automated
aliases:
  - Application Graph Automated
tags:
  - diagram
  - automation
  - knowledge-1.2
generated: 2026-07-22
sprint: Knowledge 1.2
---
# Application Graph Automated

## Overview
Auto-regenerated Mermaid diagram (Application Graph Automated) by Documentation Assistant.

## Architecture
```mermaid
flowchart TB
    __pycache__[__pycache__]
  agro_marketplace[agro_marketplace]
  auto_marketplace[auto_marketplace]
  drone_platform[drone_platform]
  port_erp[port_erp]
  __pycache__ -.-> CRM[CRM capability]

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
