---
title: Agent Graph Automated
aliases:
  - Agent Graph Automated
tags:
  - diagram
  - automation
  - knowledge-1.2
generated: 2026-07-22
sprint: Knowledge 1.2
---
# Agent Graph Automated

## Overview
Auto-regenerated Mermaid diagram (Agent Graph Automated) by Documentation Assistant.

## Architecture
```mermaid
flowchart LR
  ORCH[Orchestrator]
    ORCH --> A0[Agro AI]
  ORCH --> A1[Architect AI]
  ORCH --> A2[CRM AI]
  ORCH --> A3[Developer AI]
  ORCH --> A4[Drone Engineer AI]
  ORCH --> A5[Finance AI]
  ORCH --> A6[Legal AI]
  ORCH --> A7[Manager AI]
  ORCH --> A8[Marketplace AI]
  ORCH --> A9[Owner AI]
  ORCH --> A10[Port AI]
  ORCH --> A11[QA AI]

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
