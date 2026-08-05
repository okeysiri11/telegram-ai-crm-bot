# Enterprise Process Canon — Cross-Vertical Extensions

**Sprint:** CQ-19 — Architecture Research + Canonical Design. Documentation only, `src` not modified.

**Do not duplicate:** `docs/ENTERPRISE_SCENARIO_LIBRARY.md` (CQ-17) already scored these same eight
verticals for real-vs-SPEC backing — this document does not re-score them, it defines the **mechanism**
by which any of them (real or future) extends the canonical process without forking it.

## 1. The real mechanism already exists: `module` as extension discriminator

`deals.py`'s `Deal.module` + per-vertical `Deal*Ext` tables (`DealAgroExt`/`DealAutoExt`/`DealLegalExt`/
`DealDroneExt`/`DealFinanceExt`/`DealLogisticsExt`, `ENTERPRISE_VALUE_CHAIN.md` §1, CQ-18) and
`CalendarEvent.module` (`BUSINESS_CALENDAR.md`, CQ-17) both already establish the same real pattern: one
generic canonical entity, one `module` string discriminator, and an optional per-vertical extension
table for fields that don't generalize. Cross-vertical extension of the canonical process
(`CANONICAL_PROCESS_MODEL.md`, this sprint) reuses this exact pattern — it does not invent a plugin
system, subclass hierarchy, or schema-per-vertical design.

```ts
// SPEC — generalizes the real Deal.module / Deal*Ext pattern to the full canonical process,
// not just the sales-stage portion Deal already covers.
interface CanonicalProcessExtension {
  module: string;                    // "construction" | "healthcare" | "manufacturing" | ... — same role as Deal.module
  canonicalStage: CanonicalStage;      // real/SPEC enum, CANONICAL_PROCESS_MODEL.md §2
  extensionTable?: string;             // e.g. "DealConstructionExt" — only when fields don't generalize
  extraFields: Record<string, unknown>;
}
```

## 2. Per-vertical extension points (brief's eight, cross-referencing the CQ-17 scorecard)

| Vertical | Extension point |
|---|---|
| Construction | `execution` stage extension: `constructionSiteId` (real `LocationAssignmentKind: "construction_site"`, CQ-16) + `MovementKind: "construction_to_supplier"` (CQ-17) |
| Healthcare | `execution`/`support` extension: real `SpatialDistrictKind: "medical"` (CQ-16) only — no real `DealHealthcareExt` table exists yet, would be net-new |
| Manufacturing | `execution` extension: real `SpatialDistrictKind: "industrial"` (CQ-16) + generic `workflow_executed` payload for unit counts (CQ-17) |
| Retail | `delivery`/`support` extension: real `SpatialDistrictKind: "marketplace"` (CQ-16) only — thinnest of the eight, per `ENTERPRISE_SCENARIO_LIBRARY.md`'s own honest scoring |
| Logistics | **Real, richest** — `DealLogisticsExt` (real table, `deals.py:169`) + real `port_erp`/`port_enterprise` (`SMART_INFRASTRUCTURE.md`, CQ-16) |
| IT | `execution` extension via real `workflow_executed`/`workflow_completed` (CI/build automation) — the platform's own reference org (`ENTERPRISE_SCENARIO_LIBRARY.md` §2, CQ-17) already exercises this without any extension table |
| Crypto | **Real** — `DealFinanceExt` (real table) + `applications/crypto_enterprise` (CQ-17) |
| Legal | `contract`/`support` extension via real `applications/legal_enterprise` (`document_intelligence`, `case_management`) + `DealLegalExt` (real table) |

## 3. Adding a ninth vertical (SPEC procedure, not a new mechanism)

1. Pick a `module` string (e.g. `"hospitality"`).
2. If every canonical-stage field already generalizes, register the module with no extension table —
   exactly how IT Company operates today (§2).
3. If fields don't generalize (e.g. Construction's site/permit data), add one `Deal<Module>Ext` table,
   following the real six existing extension tables' shape.
4. No change to `CanonicalStage`, `DealPipelineStageCode`, or any core engine — the module system is
   additive by construction.

## Non-goals

- No plugin/subclass architecture — the real `module` + optional extension-table pattern is reused
  exactly.
- No new vertical scaffolding tool — `applications/enterprise_hub/business_capabilities/capabilities/*`
  (confirmed generic/uniform, CQ-17) remains a separate, thinner concept, not merged with this
  mechanism.

## Related documents

`docs/ENTERPRISE_SCENARIO_LIBRARY.md` (CQ-17, the real-vs-SPEC scorecard this reuses),
`docs/ENTERPRISE_VALUE_CHAIN.md` (CQ-18, the real `Deal.module`/`Deal*Ext` pattern this generalizes),
`docs/BUSINESS_CALENDAR.md` (CQ-17, the parallel `CalendarEvent.module` precedent),
`docs/CANONICAL_PROCESS_MODEL.md`/`docs/ENTITY_RECONCILIATION.md` (CQ-19 siblings).
