---
title: Auto Marketplace Sprint Cards
tags:
  - sprint-registry
  - knowledge-1.1
generated: 2026-07-22
---

# Auto Marketplace Sprint Cards

## Overview
Detailed sprint cards (Purpose, Features, Components, API, Architecture changes, Version, Status, Dependencies).

## Architecture
Subset of [[registries/SPRINT_REGISTRY]] with expanded columns for planning and audits.

## Components

| Sprint | Purpose | Features | Components | API | Architecture changes | Version | Status | Dependencies |
|--------|---------|----------|------------|-----|----------------------|---------|--------|--------------|
| 6.1-6.8 | First Core v3 stack | Catalog→CRM→AI→Finance→BI→Portals→Prod | auto domains | `/api/auto/v1` | First commercial app on Core v3 | lineage | completed | Core 5.x |
| 10.1-10.3 | Marketplace/VIN/AI | Listings, VIN, Auto AI | marketplace/VIN/AI | auto v1 | Expansion arc start | alpha | completed | 6.8 |
| 10.4 | Transactions | Auctions/finance/escrow | transactions | auto v1 | Commerce depth | 1.3.0-alpha | completed | 10.3 |
| 10.5 | Service | Centers/parts/warranty | service | auto v1 | Aftersales | 1.4.0-alpha | completed | 10.4 |
| 10.6 | Logistics | Transport/customs | logistics | auto v1 | Mobility logistics | 1.5.0-alpha | completed | 10.5 |
| 10.7 | Fleet | Rental/telematics | fleet | auto v1 | Fleet ops | 1.6.0-alpha | completed | 10.6 |
| 10.8 | Enterprise | Global network / commercial | enterprise | auto v1 | **2.0.0** | 2.0.0 | completed | 10.7 |


## Relationships
[[SPRINT_PROGRESS]] · [[sprints/PLATFORM]] · [[sprints/PORT_ERP]] · [[sprints/AUTO_MARKETPLACE]] · [[sprints/DRONE_PLATFORM]] · [[ROADMAP]]

## Responsibilities
Provide complete sprint metadata for living documentation.

## Interfaces
Markdown tables + registry JSON.

## REST APIs
Per-sprint API column.

## Events
Sprint completion updates.

## Future roadmap
[[ROADMAP]]

## References
[[automation/DOCUMENTATION_AUTOMATION]]

## Related pages
[[INDEX]] · [[DASHBOARD]] · [[statistics/STATISTICS]]
