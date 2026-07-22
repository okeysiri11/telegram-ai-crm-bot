---
title: Workflow Engine Detail
aliases:
  - Workflow Engine Detail
tags:
  - diagram
  - architecture
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Workflow Engine Detail

## Overview
Workflow and task engine structure.

## Architecture
```mermaid
stateDiagram-v2
  [*] --> Created
  Created --> Running
  Running --> Waiting
  Waiting --> Running
  Running --> Completed
  Running --> Failed
  Failed --> Recovered
  Recovered --> Running
  Completed --> [*]
```

## Components
- Canonical: [[Workflow Engine]]

## Relationships
[[ARCHITECTURE_DASHBOARD]] · [[ARCHITECTURE]] · [[INDEX]] · [[Platform Core]] · [[AI Agents]]

## Responsibilities
Visualize structure for Obsidian and engineering onboarding.

## Interfaces
Mermaid diagram rendered in Obsidian.

## REST APIs
See [[registries/API_REGISTRY]] when applicable.

## Events
N/A (documentation diagram).

## Future roadmap
Keep diagrams aligned after each sprint via [[automation/DOCUMENTATION_AUTOMATION]].

## References
`docs/architecture.md` and app docs.

## Related pages
[[DASHBOARD]] · [[diagrams/PLATFORM_GRAPH]] · [[diagrams/APPLICATION_GRAPH]]
