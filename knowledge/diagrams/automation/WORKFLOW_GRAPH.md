---
title: Workflow Graph
aliases:
  - Workflow Graph
tags:
  - diagram
  - automation
  - knowledge-1.2
generated: 2026-07-22
sprint: Knowledge 1.2
---
# Workflow Graph

## Overview
Auto-regenerated Mermaid diagram (Workflow Graph) by Documentation Assistant.

## Architecture
```mermaid
stateDiagram-v2
  [*] --> Detect
  Detect --> Diff
  Diff --> IncrementalUpdate
  IncrementalUpdate --> Validate
  Validate --> Snapshot
  Snapshot --> [*]

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
