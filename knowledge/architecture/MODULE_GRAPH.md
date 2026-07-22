---
title: Module Graph
aliases:
  - Module Graph
tags:
  - architecture
  - diagram
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# Module Graph

## Overview
Module mind map for major layers.

## Architecture
Auto-generated architecture visualization (Knowledge 2.2).

## Components
```mermaid
mindmap
  root((Modules))
    Platform
      platform_agents
      platform_ai
    Ecosystem
      identity
      assistant
    Knowledge
      tools
      dashboards

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
