# Agro Marketplace

---
[[INDEX]] · [[ARCHITECTURE]] · [[diagrams/APPLICATION_GRAPH]] · [[API_REFERENCE]]


## Overview
**Agro Marketplace** (`applications/agro_marketplace/`) version **2.0.0** — commercial agricultural trading platform. Sprints **8.1–8.8**. Depends on Platform Core v3 and Ecosystem v1.5 via bridges.

## Architecture
Facade: `AgroMarketplaceApplication`. Covers farmers/buyers/suppliers, catalog/harvest/warehouse, CRM/trading, export logistics, agro AI, analytics, and portals.

## Components
- Catalog, warehouse, inventory, harvest, quality
- CRM, marketplace trading, negotiations, contracts
- Export, shipping, ports, insurance, finance
- Agro AI / forecasting / agents
- Analytics, BI, dashboards
- Portal, mobile, partner API, webhooks, ops

## Relationships
- May interoperate with [[applications/PORT_ERP]] and [[applications/AUTO_MARKETPLACE]] via bridges only
- CRM patterns: [[applications/CRM]]
- Docs: `docs/AGRO_MARKETPLACE.md`, `AGRO_*.md`

## APIs
`/api/agro/v1` (+ mobile, partner, internal, webhooks prefixes)

## Future roadmap
Stronger Port ERP trade corridors and Ecosystem knowledge sync ([[ROADMAP]]).
