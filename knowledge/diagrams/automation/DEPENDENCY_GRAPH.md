---
title: Dependency Graph
aliases:
  - Dependency Graph
tags:
  - diagram
  - automation
  - knowledge-1.2
generated: 2026-07-22
sprint: Knowledge 1.2
---
# Dependency Graph

## Overview
Auto-regenerated Mermaid diagram (Dependency Graph) by Documentation Assistant.

## Architecture
```mermaid
flowchart BT
  APPS[Applications]
  ECO[Ecosystem]
  CORE[Platform Core]
  APPS --> ECO --> CORE
  APPS --> CORE
  subgraph PlatformPackages
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
  end
  CORE --> PlatformPackages

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
