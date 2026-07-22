# Port ERP

---
[[INDEX]] · [[ARCHITECTURE]] · [[diagrams/APPLICATION_GRAPH]] · [[API_REFERENCE]]


## Overview
**Port ERP** (`applications/port_erp/`) version **2.0.0** — enterprise port operations, trade, logistics, AI ops, and finance. Sprints **9.1–9.8**. Summary: [[sprints/PORT_ERP]].

## Architecture
Facade: `PortERPApplication` with domain engines for tracking, terminal operations, customs, multimodal logistics, digital twin/AI, finance, and enterprise network.

## Components
- Port core: ports, terminals, berths, vessels, voyages, cargo, containers, gates
- Live tracking (AIS/GPS)
- Yard / warehouse / gate operations
- Customs and trade documents
- Multimodal logistics
- Digital twin / executive AI ops
- Billing, contracts, tariffs, accounting
- Global network / partners / production release

## Relationships
- Bridges to Platform Core and Ecosystem
- Trade adjacency with [[applications/AGRO_MARKETPLACE]]
- Docs: `docs/PORT_ERP.md`, `PORT_*.md`

## APIs
`/api/port/v1` (+ internal, webhooks)

## Future roadmap
Expanded digital exchange and multi-port network federation ([[ROADMAP]]).

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
