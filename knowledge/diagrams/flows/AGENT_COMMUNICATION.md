---
title: Agent Communication
aliases:
  - Agent Communication
tags:
  - diagram
  - flow
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Agent Communication

## Overview
Agent Communication Mermaid diagram for Knowledge 1.1.

## Architecture
```mermaid
sequenceDiagram
  participant U as User/System
  participant ASST as Assistant
  participant ORCH as Orchestrator
  participant A as Domain Agent
  participant MEM as Memory
  U->>ASST: request
  ASST->>ORCH: TaskRequest
  ORCH->>A: delegate
  A->>MEM: remember/recall
  A-->>ORCH: result
  ORCH-->>ASST: response
  ASST-->>U: answer
```

## Components
- Related: [[diagrams/DATA_FLOW]] · [[AI Agents]]

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
