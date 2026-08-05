# Enterprise Operations — Company Operating Modes

**Sprint:** CQ-17 — Architecture Research. Documentation only, `src` not modified.

**Do not duplicate:** Real `LocationAssignmentKind` (`spatialTypes.ts`, Sprint 29.4, cited in
`REGIONAL_DIGITAL_TWIN.md`, CQ-16) already enumerates most of the brief's operating modes as location
kinds. This document maps company-level operating modes onto that real enum plus real `LifePresence`
(Sprint 29.2) rather than inventing a parallel "operating mode" field.

## 1. Per-mode mapping (brief's nine)

| Brief mode | Real foundation |
|---|---|
| Office | Real `LocationAssignmentKind: "company_office"` (`spatialTypes.ts:63`) + `LifePresence: "working"` |
| Remote | Real `LocationAssignmentKind: "remote_workplace"` + `LifePresence: "remote"` — already bridged to a real `virtual_space` entity (`spv_remote`, `REGIONAL_DIGITAL_TWIN.md` §0) |
| Hybrid | **Not a new mode** — a citizen alternating between `"company_office"` and `"remote_workplace"` assignments over time; the real `LocationAssignment.since`/`.until` fields already make this a time-series query, not a new state |
| Field Teams | Real `LocationAssignmentKind: "dynamic"` + real `setDynamicPosition()` (`spatialRuntime.ts:193-201`) — already models a worker whose location isn't a fixed building |
| Construction Sites | Real `LocationAssignmentKind: "construction_site"` + real `MovementKind: "construction_to_supplier"` (`DAILY_OPERATIONS_MODEL.md`) — genuinely real, not SPEC, confirmed this sprint |
| Warehouse Operations | Real `LocationAssignmentKind: "warehouse"` + real `MovementKind: "warehouse_to_client"` + real `multi_company.Branch.shared_inventory` (CQ-15) for multi-branch stock sharing |
| Retail | **No dedicated real mode** — closest real anchor is `SpatialDistrictKind: "marketplace"` (`REGIONAL_DIGITAL_TWIN.md` §1) for location, and the generic, templated `business_capabilities/capabilities/*.py` scaffold pattern (confirmed this sprint to be uniform boilerplate — same KPI/AI-component shape per domain, no differentiated retail logic) — flagged as thin, not fabricated as deep |
| Manufacturing | Real `SpatialDistrictKind: "industrial"` for location; "Production" events are real but generic (`workflow_executed`/`workflow_completed`, `DAILY_OPERATIONS_MODEL.md` §1) — no dedicated manufacturing-output data model exists |
| Service Companies | **No dedicated real mode** — maps to `SpatialDistrictKind: "business"` for location; a service company's real distinguishing signal is `BusinessProfile.category` (Sprint 29.0), not a new operating-mode field |

## 2. Operating mode as a derived read, not a stored field

```ts
// SPEC — operating mode is computed, never stored, from real LocationAssignment history:
function deriveOperatingMode(assignments: LocationAssignment[]): CompanyOperatingMode {
  // e.g. >90% "company_office" over 30d → "office"; mixed → "hybrid";
  // presence of any "construction_site"/"warehouse"/"dynamic" assignment → that mode, additively
  // (a company can be Warehouse Operations AND Hybrid at once — modes are not mutually exclusive)
}
```

This mirrors `CITY_LIVING_ECONOMY.md`'s (CQ-10) `BusinessTier` discipline: a signal computed from real,
verifiable inputs, never a self-declared flag a company can set directly.

## Non-goals

- No new `LocationAssignmentKind`/`operatingMode` field on any entity — every mode above is either a
  real existing kind or a derived aggregate over real assignment history.
- No fabricated Retail/Manufacturing/Service business logic — the generic capability-seed scaffolding
  found this sprint is cited honestly as thin, not built out here.

## Related documents

`docs/REGIONAL_DIGITAL_TWIN.md` (CQ-16, real `LocationAssignmentKind`), `docs/DAILY_OPERATIONS_MODEL.md`
(CQ-17 sibling, real `MovementKind`), `docs/CROSS_COMPANY_OPERATIONS.md` (CQ-15, real `Branch.shared_
inventory`), `docs/CITY_LIVING_ECONOMY.md` §1.3 (CQ-10, the derived-signal discipline reused in §2),
`docs/ENTERPRISE_SCENARIO_LIBRARY.md` (CQ-17 sibling — concrete companies exercising these modes).
