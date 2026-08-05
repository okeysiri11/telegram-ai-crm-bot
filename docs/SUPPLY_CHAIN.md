# Enterprise Value Chain — Supply Chain

**Sprint:** CQ-18 — Architecture Research. Documentation only, `src` not modified.

**Do not duplicate:** `docs/TENDERS_PROCUREMENT.md` (CQ-13) already generalized real tender/bid/auction
precedents (`FREIGHT_EXCHANGE.md`, `AUCTION_PLATFORM.md`) — this document does not repeat that. Real
`docs/AGRO_SUPPLY_CHAIN.md` (Sprint 14.5) already covers agro-vertical supply chain — cited, not
redesigned. This document's contribution is mapping the brief's eight supply-chain items onto real
procurement and warehouse code, and naming the one clear gap: no generalized Supplier/Contractor
entity exists.

## 1. Per-item mapping (brief's eight)

| Brief item | Real/SPEC source |
|---|---|
| Suppliers | Real, vertical-scoped — `automotive_procurement.py`'s `VehicleSource`/`SupplierOffer` (automotive only). No generalized `Supplier` entity exists in `database/models/` — confirmed by direct search this sprint |
| Contractors | **Absent** — no real contractor entity anywhere; a Construction scenario (`ENTERPRISE_SCENARIO_LIBRARY.md`, CQ-17) would need this generalized entity first |
| Subcontractors | **Absent**, same gap as Contractors — structurally would reuse `OwnershipEdge`'s discriminator pattern (`EBN_BUSINESS_GRAPH.md`, CQ-10) if modeled as a company-to-company relationship, or a new SPEC entity if modeled as an individual — not decided here |
| Warehouses | **Real, substantial** — `applications/port_enterprise/warehouse_distribution/warehouse.py`'s real `WarehouseManagement` (`register_warehouse`, `create_zone`, `receive`, `ship`, `cross_dock`, `cold_storage`, `hazardous_storage`, `optimize_inventory`), `DistributionCenters`, `FreeEconomicZones` |
| Procurement | Real `automotive_procurement.py`'s `PurchaseOrder`/`PurchaseOrderStatus` (automotive-scoped); `docs/TENDERS_PROCUREMENT.md` (CQ-13) is the correct real generalization target for non-automotive procurement |
| Deliveries | Real `vehicle_assigned`/`MovementKind: "warehouse_to_client"` (`DAILY_OPERATIONS_MODEL.md`, Sprint 29.2) |
| Inventory | Real `WarehouseManagement.optimize_inventory` + real `automotive_inventory.py` (vehicle-specific) |
| Logistics | Real `applications/port_erp` (AIS/GPS/geofence) + `applications/port_enterprise/multimodal_logistics` (incl. real rail, `SMART_INFRASTRUCTURE.md`, CQ-16) |

## 2. The one real gap: no generalized Supplier/Contractor entity

Every real system in §1 is either automotive-scoped (`automotive_procurement.py`) or logistics/
warehouse-scoped (`port_erp`/`port_enterprise`) — none is a generic cross-vertical "who supplies this
company" entity. This mirrors `SUPPLY_CHAIN.md`'s (this document) own finding at a smaller scale: the
same generic-entity-plus-module pattern that worked for `Deal`/`CalendarEvent` has not yet been applied
here.

```ts
// SPEC — mirrors the real Deal.module / CalendarEvent.module generalization pattern.
interface Supplier {
  id: string;
  companyId?: string;              // real BusinessProfile.id, if the supplier is itself an EBN company
  module: string;                  // "automotive" | "construction" | "warehouse" | ... — same discriminator role as Deal.module
  relationshipKind: "supplier" | "contractor" | "subcontractor";
  metadata: Record<string, unknown>;
}
```

`relationshipKind: "subcontractor"` composes with the real `OwnershipEdge` pattern
(`EBN_BUSINESS_GRAPH.md`, CQ-10) when the subcontractor is itself a tracked `BusinessProfile`, exactly
as `TERRITORIAL_GOVERNANCE.md` (CQ-16) reused that pattern for Business Associations/Economic Clusters.

## Non-goals

- No new procurement/tender engine — `TENDERS_PROCUREMENT.md` (CQ-13) remains the canonical
  generalization target.
- No new warehouse/logistics engine — `WarehouseManagement`/`port_erp` remain authoritative.
- No implementation of the `Supplier` SPEC entity — named and shaped, not built, per this sprint's
  documentation-only constraint.

## Related documents

`docs/TENDERS_PROCUREMENT.md`/`docs/AGRO_SUPPLY_CHAIN.md` (CQ-13/real, the procurement precedents this
extends), `docs/SMART_INFRASTRUCTURE.md` (CQ-16, real port/rail/warehouse infrastructure),
`docs/EBN_BUSINESS_GRAPH.md` (CQ-10, `OwnershipEdge` pattern reused for subcontractors),
`docs/ENTERPRISE_VALUE_CHAIN.md`/`docs/RESOURCE_ORCHESTRATION.md` (CQ-18 siblings).
