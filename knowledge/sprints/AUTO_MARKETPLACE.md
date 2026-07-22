# Auto Marketplace Sprints

---
[[INDEX]] · [[PLATFORM_TIMELINE]] · [[CHANGELOG]] · [[ROADMAP]]


## Overview
Two completed arcs: **6.1–6.8** (first Platform v3 commercial stack) and **10.1–10.8** (marketplace expansion to **2.0.0**). App: [[applications/AUTO_MARKETPLACE]].

## Architecture
Progressive domain facades on `AutoMarketplaceApplication`, always integrating via bridges (no Agro/Port/Core mutations).

## Components

### Sprints 6.1–6.8 — Core product stack
| Sprint | Focus |
|--------|-------|
| 6.1 | Foundation / catalog baseline |
| 6.2 | Vehicle catalog depth |
| 6.3 | CRM engine |
| 6.4 | AI sales |
| 6.5 | Finance engine |
| 6.6 | Business intelligence |
| 6.7 | Customer/dealer portals |
| 6.8 | Production release |

Docs: `VEHICLE_CATALOG.md`, `CRM_ENGINE.md`, `AI_SALES.md`, `FINANCE_ENGINE.md`, `BUSINESS_INTELLIGENCE.md`, `CUSTOMER_PORTAL.md`, `PRODUCTION_RELEASE.md`

### Sprints 10.1–10.8 — Expansion to commercial 2.0.0
| Sprint | Focus | Version marker |
|--------|-------|----------------|
| 10.1 | Marketplace foundation / search / dealers | alpha lineage |
| 10.2 | VIN / history / dealer network | |
| 10.3 | Auto AI intelligence | |
| 10.4 | Auctions, financing, leasing, insurance, escrow | 1.3.0-alpha |
| 10.5 | Service centers, parts, warranty | 1.4.0-alpha |
| 10.6 | Transport, carriers, customs logistics | 1.5.0-alpha |
| 10.7 | Fleet, rental, telematics, AI ops | 1.6.0-alpha |
| 10.8 | Enterprise connectors, global network, commercial **2.0.0** | 2.0.0 |

Docs: `AUTO_MARKETPLACE.md`, `AUTO_VIN.md`, `AUTO_AI.md`, `AUTO_TRANSACTIONS.md`, `AUTO_SERVICE.md`, `AUTO_LOGISTICS.md`, `AUTO_FLEET.md`, `AUTO_ENTERPRISE.md`, `AUTO_RELEASE.md`

## Relationships
- Parallel commercial peers: Agro 8.x, Port 9.x
- CRM capability page: [[applications/CRM]]

## APIs
`/api/auto/v1` family — [[API_REFERENCE]]

## Future roadmap
Ecosystem-wide registration and cross-vertical commerce ([[ROADMAP]]).
