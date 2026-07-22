# Auto Marketplace

---
[[INDEX]] · [[ARCHITECTURE]] · [[diagrams/APPLICATION_GRAPH]] · [[API_REFERENCE]]


## Overview
**Auto Marketplace** (`applications/auto_marketplace/`) is a commercial vehicle marketplace and mobility platform at version **2.0.0** (`production_ready`). Built on Platform Core v3 and Ecosystem v1.5 via bridges. Sprint arcs: **6.1–6.8** (first Core v3 app) and **10.1–10.8** (marketplace expansion). See [[sprints/AUTO_MARKETPLACE]].

## Architecture
Facade: `AutoMarketplaceApplication`. Domains include vehicle catalog, CRM, AI sales, marketplace/VIN, transactions, service, logistics, fleet, enterprise release. Integrates Agro/Port optionally through outbound bridges without modifying those apps.

## Components
- Vehicle catalog, inventory, media, search
- CRM / sales pipeline / AI sales assistant
- Marketplace listings, dealers, VIN/history
- Auctions, financing, leasing, insurance, escrow, payments
- Service centers, parts, warranty, diagnostics
- Transport, customs, fleet/rental, telematics
- BI, portals, mobile/partner APIs, enterprise/global network

## Relationships
- Bridges: platform + ecosystem (+ optional agro/port)
- Related: [[applications/CRM]], [[applications/AGRO_MARKETPLACE]], [[applications/PORT_ERP]]
- Docs: `docs/AUTO_MARKETPLACE.md`, `AUTO_*.md`, `VEHICLE_CATALOG.md`, `CRM_ENGINE.md`

## APIs
Primary: `/api/auto/v1`  
Also: `/api/auto/mobile/v1`, `/api/auto/partner/v1`, portal, `/internal/auto/v1`, `/webhooks/auto/v1`

## Future roadmap
Deeper Ecosystem registration, cross-border commerce, shared CRM fabric with other verticals ([[ROADMAP]]).

## Responsibilities
Document and navigate this concern within the Obsidian living vault (Knowledge 1.1).

## Interfaces
Wiki links, dashboards, and registries. Runtime interfaces described where applicable.

## REST APIs
See [[registries/API_REGISTRY]] and [[API_REFERENCE]] when this page owns HTTP surfaces; otherwise N/A.

## Events
Domain or documentation events as applicable; see related sprint pages.

## References
Repository `docs/`, manifests, [[standards/DOCUMENTATION_STANDARDS]].

## Related pages
[[INDEX]] · [[DASHBOARD]] · [[ROADMAP]] · [[registries/COMPONENT_REGISTRY]]
