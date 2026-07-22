---
title: Technical Debt
aliases:
  - Technical Debt
tags:
  - debt
  - architecture
  - knowledge-1.3
generated: 2026-07-22
sprint: Knowledge 1.3
---
# Technical Debt

## Overview
Technical debt register generated 2026-07-22 from Architecture Guardian.

## Architecture
Debt is classified by severity; knowledge tools only document — they do not auto-refactor runtime code.

## Components
### High priority
- cross_app_import: `applications.auto_marketplace` imports `applications.port_erp` — prefer bridges only (`applications.auto_marketplace`)
- cross_app_import: `applications.auto_marketplace` imports `applications.agro_marketplace` — prefer bridges only (`applications.auto_marketplace`)
**Estimated effort:** 4–8 engineering-hours (est.)

### Medium priority
- None
**Estimated effort:** 1–2 engineering-hours (est.)

### Low priority
- dead_documentation: reports/DAILY_NOTES_INDEX.md
- dead_documentation: diagrams/architecture/DRONE_PLATFORM_DETAIL.md
- dead_documentation: diagrams/architecture/AUTO_MARKETPLACE_DETAIL.md
- dead_documentation: diagrams/architecture/AGRO_MARKETPLACE_DETAIL.md
- dead_documentation: diagrams/architecture/PORT_ERP_DETAIL.md
- dead_documentation: diagrams/architecture/WORKFLOW_ENGINE_DETAIL.md
- dead_documentation: diagrams/architecture/LEGAL_PLATFORM_DETAIL.md
- dead_documentation: diagrams/architecture/PLATFORM_CORE_DETAIL.md
- dead_documentation: diagrams/architecture/CRM_DETAIL.md
- dead_documentation: diagrams/architecture/PLUGIN_SDK_DETAIL.md
- dead_documentation: diagrams/architecture/MEMORY_ENGINE_DETAIL.md
- dead_documentation: diagrams/flows/ENTITY_RELATIONSHIPS.md
- dead_documentation: sprints/registry/DRONE_PLATFORM_SPRINTS.md
- dead_documentation: sprints/registry/PORT_ERP_SPRINTS.md
- dead_documentation: sprints/registry/PLATFORM_CORE_SPRINTS.md
- dead_documentation: sprints/registry/FUTURE_PLATFORMS.md
- dead_documentation: sprints/registry/AUTO_MARKETPLACE_SPRINTS.md
**Estimated effort:** 8–17 engineering-hours (est.)

## Relationships
[[ARCHITECT_RECOMMENDATIONS]] · [[PROJECT_HEALTH]] · [[DEPENDENCY_REPORT]]

## Responsibilities
Make debt visible for sprint planning.

## Interfaces
`python3 knowledge/tools/technical_debt.py`

## REST APIs
N/A

## Events
technical_debt_updated

## Future roadmap
[[ROADMAP]]

## References
Guardian violations + circular/orphan/dead-doc detectors

## Related pages
[[EXECUTIVE_DASHBOARD]] · [[INDEX]]
