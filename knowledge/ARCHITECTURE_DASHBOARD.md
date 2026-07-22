---
title: Architecture Dashboard
aliases:
  - Architecture Dashboard
tags:
  - dashboard
  - knowledge-1.3
generated: 2026-07-22
sprint: Knowledge 1.3
---
# Architecture Dashboard

## Overview
Auto-updated for Knowledge 1.3 Architecture Guardian — Architecture Dashboard.

## Architecture
Scores and health derived from read-only repository analysis.

## Components
**Architecture Quality Score:** 84.0
**Coupling / Cohesion:** 42.0 / 100.0
**Risk:** Low

### Guardian outputs
[[DEPENDENCY_REPORT]] · [[ARCHITECT_RECOMMENDATIONS]] · [[TECHNICAL_DEBT]] · [[PROJECT_HEALTH]] · [[ARCHITECTURE_HISTORY]]
[[reports/ARCHITECTURE_GUARDIAN]] · [[automation/ARCHITECTURE_GUARDIAN]]

### Graphs
[[diagrams/automation/DEPENDENCY_GRAPH]] · [[diagrams/automation/ARCHITECTURE_GRAPH]]

## Relationships
[[automation/ARCHITECTURE_GUARDIAN]] · [[PROJECT_HEALTH]]

## Responsibilities
Surface architecture quality to the vault.

## Interfaces
`full_architecture_review.py`

## REST APIs
[[registries/API_REGISTRY]]

## Events
dashboard_updated_from_guardian

## Future roadmap
[[ROADMAP]]

## References
Architecture scores JSON

## Related pages
[[INDEX]] · [[TECHNICAL_DEBT]]
