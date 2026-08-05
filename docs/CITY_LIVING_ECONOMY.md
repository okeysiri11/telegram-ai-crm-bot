# Enterprise Business Network — Living Enterprise City & Digital Odessa

**Sprint:** CQ-10 — Architecture Research + Game Design Research + Product Research. Documentation
only, `src` not modified.

**Do not duplicate:** Every rendering/animation/camera/layer mechanism this document invokes is real
and already specified across CG-2 through CG-9 — this document adds *business-activity triggers* onto
those real mechanisms, never a new rendering system. `CITY_SIMULATION.md` §5 (CG-9) already built a
ten-driver "how the city changes" scorecard for *technical/AI* activity; this document is that same
exercise for *business* activity specifically, and cross-references rather than repeats it.

## 1. Living Enterprise City — business activity as a city-change driver

### 1.1 The one rule this whole section obeys

`ENTERPRISE_BUSINESS_NETWORK.md` §0 items 1–2, restated as the literal design constraint: **every
visual change traces to a real business fact, and nothing is ever removed, only re-rendered.** The
brief's six examples (buildings evolve, headquarters grow, transportation increases, districts become
more active, business traffic increases, AI agents move, workflow flows become visible) are mapped
below to real mechanisms or clearly-scoped SPEC extensions — never a decorative "growth" animation
detached from data.

### 1.2 Per-example mapping

| Brief example | Real mechanism it extends | SPEC extension |
|---|---|---|
| Buildings evolve | `CITY_BUILDING_STATES.md` (CG-4) real Lifecycle/Health/Interaction axes | **New axis, not a fourth flat state**: a `BusinessTier` (see §1.3) driving building *visual scale/prominence*, independent of and additive to the existing three axes |
| Headquarters grow | Same `BusinessTier` mechanism, applied specifically to a company's `headquartersBuildingId` | A headquarters' tile size/prominence scales with `BusinessTier`, reusing the real `CityBuilding.w/h` percentage-space sizing (`cityCatalog.ts`) — a **data-driven size multiplier**, not a new geometry system |
| Transportation increases | `CITY_VISUAL_STATES.md` §3–4 (CG-9, drones/delivery-robot markers — themselves a skin on the one real traveling-object mechanism, `CITY_SIMULATION.md` §2.2) | Trigger source becomes `Partnership` activity (`EBN_PARTNERSHIP_SYSTEM.md`) in addition to the AI/job triggers CG-9 already specified — same marker, new real trigger |
| Districts become more active | `CITY_SIMULATION.md` §1.2's proposed `DistrictRuntimeSummary` aggregation (CG-4) | Extend the aggregate with a `businessActivityCount` (partnerships formed, documents signed, timeline events) alongside the existing health/lifecycle counts |
| Business traffic increases | `CITY_VISUAL_STATES.md` §1 (CG-9) real `.ec-link-line.is-flowing` | Trigger source becomes Business Graph edges (`EBN_BUSINESS_GRAPH.md` §3) at `trustTier: "strategic"`, in addition to the existing focused-building/workflow-path triggers |
| AI agents move | `CITY_SIMULATION.md` §2.2 (CG-4), already real-spec'd, unchanged by this document | Not extended — this remains purely a technical/AI-activity signal, not a business one; restated only to confirm this document does not conflate the two |
| Workflow flows become visible | `SPRINT_CG_9_RESULT.md` discovery #4 (CG-9) — the real `cityPath` field on workflow templates, currently only feeding simulated data | Once wired to a real running workflow (`AUTOMATION_ENGINE.md`, CG-7/real Sprint 28.9 implementation), a **business** workflow specifically (e.g. a partnership's document-signing flow) should render exactly the same way — one visualization mechanism for both technical and business workflows, not two |

### 1.3 `BusinessTier` (SPEC) — the one new visual axis this document introduces

```ts
type BusinessTier = "startup" | "established" | "growth" | "enterprise" | "flagship";
// SPEC — computed from real, verifiable inputs only (never a vanity metric a company can inflate directly):
// partnership count at trustTier >= "trusted", timeline event count, verification level, account age.
```

`BusinessTier` is deliberately **not** a copy of `TrustScore`/`ReputationScore`
(`ENTERPRISE_BUSINESS_NETWORK.md` §3.1–3.2) — it's a *visual prominence* signal, computed from a
blend of both (a highly-trusted but tiny company shouldn't visually dwarf a large, growing one; a
huge but unverified entity shouldn't either). Rendering effect: a headquarters building's real `w`/`h`
(percentage-space size, `CityBuilding`) scales by a fixed multiplier per tier (e.g. `startup: 1.0x`,
`flagship: 1.6x`) — bounded, so no single company can visually dominate the map regardless of scale,
consistent with `CITY_SIMULATION.md` §3's performance-budget discipline (CG-4) of fixed, sane ceilings
rather than unbounded growth.

**Nothing disappears, restated concretely**: a company that drops from `flagship` back to `growth`
(reputation event, partnership loss) shrinks its headquarters visually — it never loses the building,
never gets removed from the map, and its Timeline (`ENTERPRISE_BUSINESS_NETWORK.md` §3.4) records the
tier change as a real, visible event, not a silent regression.

## 2. Digital Odessa — the real-map foundation

### 2.1 What "Digital Twin of Odessa" means architecturally, not just narratively

Enterprise City's real building/district model (`cityCatalog.ts`, `cityDistricts.ts`, CG-2) is
**percentage-space, not geo-coordinate-space** — `CityBuilding.x/y/w/h` are abstract 0–100 map
coordinates, not latitude/longitude. This is the single most important technical fact for "Digital
Odessa" framing: **the real system today has no actual Odessa geography encoded in it.** The district
names (CRM, ERP, AI, etc., `CITY_DISTRICTS.md`, CG-9) are functional/capability districts, not
neighborhoods of the real city of Odessa. This document does not pretend otherwise — "Digital Odessa"
is the *narrative and future-visual* framing this Bible adopts (buildings could be skinned with
Odessa-inspired architecture, districts could be laid out echoing real Odessa neighborhoods), not a
claim that real GIS data already backs the map.

### 2.2 Per-concept mapping (brief's list)

| Brief concept | Real foundation | SPEC extension |
|---|---|---|
| Real map foundation | Percentage-space abstract map (real, `cityEngine.ts`) | A future skin layer mapping district positions to a stylized Odessa-inspired layout — a **visual theme**, not a coordinate-system change (keeps `CityViewport`'s real 0–100 math intact, per `CITY_CAMERA.md` §6.4's own "extend, don't replace the camera model" precedent, CG-4) |
| Districts | Real 12 (+3 SPEC), `CITY_DISTRICTS.md` (CG-9) | Odessa-flavored naming/visual skin only — no structural change |
| Buildings | Real 34, `cityCatalog.ts` | Company-claimed headquarters (`ENTERPRISE_BUSINESS_NETWORK.md` §3) are a new building *category* layered onto the existing building model, not a new geometry system |
| Roads | Real `streetGraph()` | Business Graph edges (`EBN_BUSINESS_GRAPH.md`) reuse this exactly |
| Transportation | SPEC, `CITY_VISUAL_STATES.md` §3–4 (CG-9) | Unchanged by this document |
| Companies | **New, this Bible's core contribution** | `Company` entity (`ENTERPRISE_BUSINESS_NETWORK.md` §3) |
| Logistics | No real concept found anywhere in this survey | **SPEC, lowest priority** — would model as Supplier/Dealer partnership edges (`EBN_BUSINESS_GRAPH.md`) with a delivery-robot visual (`CITY_VISUAL_STATES.md` §4) already specified; no new logistics-specific data model proposed |
| Offices | Same as headquarters — a company could plausibly claim more than one building (branch offices) | **SPEC**: `Company.branchBuildingIds?: string[]`, additive to the real single-building binding, not designed in further depth this pass — flagged as a real future need, not a near-term one |

### 2.3 Future multi-city expansion — the constraint this whole document is designed against

Per the brief's explicit requirement ("must support additional cities without changing the core
architecture"), every entity and mechanism in this Bible is checked against one question: **does this
assume there is exactly one city?**

| Entity/mechanism | Single-city assumption today? | What a second city needs |
|---|---|---|
| `Company.headquartersBuildingId` | Implicitly single-City-instance | Add `cityId` alongside `headquartersBuildingId` — additive field, no redesign |
| `CityViewport`/camera (real, CG-2) | Yes — one `CityViewport` per session (`CITY_DESKTOP.md` §2, CG-6, already found this is per-window/session anyway) | A city-switcher is a navigation-level concern (`CITY_NAVIGATION.md`, CG-9), not a camera redesign — each city keeps its own independent viewport |
| Business Graph edges (`EBN_BUSINESS_GRAPH.md`) | No inherent assumption — an edge is just two `Company` records | Cross-city edges are `EBN_BUSINESS_GRAPH.md` §4's explicitly-flagged open question, not solved here either |
| District/building catalogs (`cityCatalog.ts`, real) | Yes — one flat `CITY_BUILDINGS` array today | Would need a `cityId`-scoped catalog structure — a real, non-trivial refactor of existing code, **flagged as the one item in this entire document that would require touching real, shipped City code**, not purely additive |

**Honest conclusion**: the *business* layer (Company, Partnership, Business Graph) this Bible
specifies is designed multi-city-clean from the start (additive `cityId` fields throughout). The
*existing* City catalog structure (`cityCatalog.ts`) is not — extending it to multiple cities is real,
scoped future work this document identifies but does not perform (this sprint does not modify `src`).

## 3. Non-goals

- No real Odessa GIS/geo-coordinate data is proposed — §2.1 is explicit that the real map stays
  percentage-space; "Digital Odessa" is narrative/visual framing, not a coordinate system claim.
- No multi-city catalog refactor is designed in this pass — §2.3's table names it as a real future
  cost, not something this document solves.
- No new geometry/sizing system — `BusinessTier` (§1.3) is a multiplier on the real existing `w`/`h`
  fields.

## Related documents

`ENTERPRISE_BUSINESS_NETWORK.md` (Company entity, philosophy), `CITY_DISTRICTS.md`/`CITY_SIMULATION.md`/
`CITY_VISUAL_STATES.md`/`CITY_WORLD.md`/`CITY_NAVIGATION.md` (CG-9, the real/SPEC mechanisms this
document's every row cites), `EBN_BUSINESS_GRAPH.md` (edges this document's traffic/transportation
rows reuse), `CITY_DESKTOP.md` §2 (CG-6, the per-session viewport finding §2.3 relies on),
`AUTOMATION_ENGINE.md` (CG-7, now real per Sprint 28.9 — the workflow-visibility row's real target).

---

## Sprint CQ-13 addition — City Economy (brief §6), full reconciliation

**Do not duplicate:** every brief §6 example is already specified across this document and its CQ-11
sibling `CITY_OBJECT_MODEL.md` — this addition is a reconciliation table, not new design.

| Brief example | Already specified in |
|---|---|
| New offices | `CITY_OBJECT_MODEL.md` §2.1 (CQ-11) — a `BuildingSubtype: "office"` claim |
| Growing headquarters | §1.3 above, `BusinessTier` |
| Construction | `CITY_OBJECT_MODEL.md` §2.1 (CQ-11) — Construction Site transient state |
| Business districts | `CITY_DISTRICTS.md` D16–D19 (CQ-11) — the real-vertical-grounded district specialization |
| Advertising | `CITY_VISUAL_STATES.md` §8 (CG-9), `EBN_GAMIFICATION_MONETIZATION.md` §2/§4 (CQ-10) |
| Business traffic | §1.2 above, road-flow at `trustTier: "strategic"` |
| Logistics | `CITY_DISTRICTS.md` D19 (CQ-11, real `port_erp`/`port_enterprise` grounding), `CITY_OBJECT_MODEL.md` §3's `ship` `VehicleKind` |
| Supply chains | `EBN_BUSINESS_GRAPH.md` §1 (CQ-10) — `supplier`/`customer` `RelationshipType` edges, rendered as Business Graph roads |
| Service activity | `ENTERPRISE_ECONOMY.md` §4 (CQ-13, `ServiceListing`) — new this sprint, the one item without a prior real/SPEC home |

No new mechanism is required for eight of the nine examples — this table exists so a reader arriving
at "City Economy" doesn't need to re-derive what's already been designed across three prior sprints.
