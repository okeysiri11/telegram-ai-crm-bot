---
title: Architecture Dashboard
aliases:
  - Architecture Dashboard
tags:
  - dashboard
  - knowledge-1.2
generated: 2026-07-22
sprint: Knowledge 1.2
---
# Architecture Dashboard

## Overview
Automatically updated dashboard (Architecture Dashboard) — Knowledge 1.2.

## Architecture
Driven by Documentation Assistant incremental sync.

## Components
### Automated graphs
[[diagrams/automation/ARCHITECTURE_GRAPH]] · [[diagrams/automation/DEPENDENCY_GRAPH]] · [[diagrams/automation/WORKFLOW_GRAPH]]
[[diagrams/automation/AGENT_GRAPH]] · [[diagrams/automation/APPLICATION_GRAPH]] · [[diagrams/automation/DEPLOYMENT_GRAPH]]
[[diagrams/automation/API_GRAPH]] · [[diagrams/automation/KNOWLEDGE_GRAPH]]

### Diff
[[ARCHITECTURE_CHANGES]]

### Classic diagrams
[[diagrams/PLATFORM_GRAPH]] · [[diagrams/APPLICATION_GRAPH]] · [[diagrams/AGENT_GRAPH]] · [[diagrams/DATA_FLOW]]

## Relationships
[[INDEX]] · [[DASHBOARD]] · [[automation/DOCUMENTATION_ASSISTANT]]

## Responsibilities
Keep stakeholders synchronized with project state.

## Interfaces
`python3 knowledge/tools/update_dashboards.py`

## REST APIs
[[registries/API_REGISTRY]]

## Events
dashboard_updated

## Future roadmap
[[ROADMAP]]

## References
Git + snapshot

## Related pages
[[VALIDATION_REPORT]] · [[reports/PROJECT_REPORT]]
