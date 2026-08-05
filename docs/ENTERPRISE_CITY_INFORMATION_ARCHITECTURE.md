# Enterprise City 2D — Information Architecture

**Role:** Lead UX Architect & Digital Twin Architect. Documentation only, no code written.

## 1. Visual model — what each element represents

| City element | Represents | Real/new |
|---|---|---|
| Building | A module or vertical capability (CRM, ERP, a company's HQ) | Real pattern (`cityCatalog.ts`), extended to new districts |
| Road | A workflow — the real `streetGraph()` already connects buildings; a business workflow traversing multiple modules renders as a flow along the same real road graph | Real infrastructure, `docs/CITY_LIVING_ECONOMY.md`'s (CQ-10) already-designed reuse |
| District | A domain boundary — CRM district, Legal district, a vertical's district | Real, extended per §3 below |
| User movement | A citizen's real `LocationAssignment`/`LifePresence` rendered as a marker moving building-to-building, driven by real `cityMovement`/`MovementKind` | Real (`DAILY_OPERATIONS_MODEL.md`) |
| AI agent movement | Same real movement mechanism, `actorAiId` instead of `actorCitizenId` — already a real field on `CityMovement` | Real, same mechanism as users, not a separate one |
| Notifications | A transient marker/pulse on the relevant building, sourced from the real composed notification model (`docs/OPERATIONAL_NOTIFICATIONS.md`) | Composition of real data, new visual treatment |
| Tasks | A real task's building-adjacent badge/counter (pending `TD-50`'s task-model reconciliation for which "task" is canonical) | Partially real, partially blocked on existing debt |
| CRM entities | A real `Deal`'s stage renders as the deal's position along a CRM-district "pipeline road" — a literal visual pipeline, using the real `DealPipelineStageCode` order | New visual treatment of real data |
| Projects | Once `TD-51`'s `Project` entity exists, a project renders as a construction-state building (per the real `construction_site` `LocationAssignmentKind`, CQ-16) — until then, a marker on the real `ProjectParticipant`-tracked location | Partially blocked, degrades gracefully today |
| Department connections | Roads between department buildings, weighted by real interaction volume (`businessInteractions` count) — busier roads render more prominent, per the real traffic-flow visual trigger already established (`CITY_VISUAL_STATES.md`, CG-9) | Real mechanism, new specific application |

## 2. How the city scales from one company to thousands

This is the brief's most architecturally consequential ask. Three tiers, each with a different visual
strategy — not one strategy stretched thin:

| Scale | Strategy |
|---|---|
| One company (current default, "Odessa" reference) | Full detail — every building individually rendered, current model unchanged |
| Tens to hundreds of companies | **District-of-districts** — each company gets a real `SpatialEntity` region (already the real Spatial Runtime model, CQ-16) rendered as a compact cluster; zooming into a cluster reveals its internal district layout | New rendering behavior, reuses the existing real hierarchy (`Country → Region → City → District`) one level up — a *city of cities*, not a redesign of the per-company view |
| Thousands of companies | **Clustering + LOD, not individual rendering** — at this scale, individual buildings are never drawn; only aggregate markers (real `BusinessTier`-weighted, `CITY_LIVING_ECONOMY.md` §1.3) are, with real drill-down on selection. This is the same principle every real map application (Google Maps, GitHub's repo graphs) uses at high entity counts, and is the load-bearing reason a real 2D engine (not DOM) is required — see the rendering-architecture companion | New, required at this scale |

**The critical architectural point**: this is not "render everything and hope it's fast" — it's a
real LOD (level-of-detail) discipline, matching the one already proven in the City's own Graphics
Engine design (`docs/CITY_SIMULATION.md`, CG-4/CG-9) and extended here from "one city's rendering
cost" to "how many cities are visible at once."

## 3. District coverage — closing the real gap found this review

Confirmed this review: the real 16-district Sprint 30.4 set has no dedicated district for Crypto OTC,
Drone Engineering, Agro Trading, Cafe & Beauty, Medical, or Construction, despite real backend verticals
existing for the first three. Recommended new districts, using the real `module`-discriminator pattern
already established (`docs/CROSS_VERTICAL_EXTENSIONS.md`, CQ-19) rather than a bespoke per-district
mechanism:

| New district | Backs | Real/SPEC |
|---|---|---|
| Crypto Exchange | `crypto_enterprise` | Real backend, new district needed |
| Drone Operations | `drone_platform` | Real backend, new district needed |
| Agro Trading | `agro_enterprise` | Real backend, new district needed |
| Cafe & Beauty | Real `CPL_LOYALTY_CALENDAR.md`-adjacent capability | Real-ish backend (loyalty/membership), thin elsewhere, per `docs/CUSTOMER_JOURNEY.md` §3 |
| Medical, Construction, Manufacturing (as distinct from generic Production) | No dedicated real vertical | SPEC only — per `docs/ENTERPRISE_SCENARIO_LIBRARY.md`'s (CQ-17) honest scoring, these districts should exist as placeholders with visibly thinner detail, not implied parity with CRM/ERP |
| Partner Portal | Real `Relationship`/Business Network cross-org data | Real backend, new district (currently folded implicitly into other districts) |
| Developer Center | Real `/platform-builder/*` routes, real `platform_console` | Real, currently exists as "Developer Zone" — rename consideration, not a new district |
| Owner Dashboard / Command Center | Real Owner nav (`docs/OWNER_EXPERIENCE.md`) | Already real as a mode overlay, not itself a spatial district — correctly kept as a UI mode, not forced into a building metaphor it doesn't fit |

## 4. Map generation — evaluating the brief's six options

| Option | Description | Assessment |
|---|---|---|
| A. Hand-crafted | Fixed, designer-placed districts/buildings (the current real approach) | Best for the single-company reference city — full creative control, but doesn't scale to option-required territory (thousands of companies) without per-company manual work |
| B. Generated from company structure | Layout derived from real org chart (`Membership`/department hierarchy) | Strong fit for the *per-company* internal layout — a real, structured input already exists (`CITIZEN_ORGANIZATION_MEMBERSHIP.md`, CQ-12) |
| C. Generated from CRM relationships | Layout derived from real `Relationship`/Business Graph edges | Strong fit for the *inter-company* view (Partner Portal, cross-org districts) — real data (`EBN_BUSINESS_GRAPH.md`, CQ-10) already models exactly this graph |
| D. Generated from GIS/OpenStreetMap | Real-world map data | **Not recommended** — this engagement's own CQ-10 research already concluded "Digital Odessa" is deliberately narrative, not real GIS-backed (`docs/CITY_LIVING_ECONOMY.md` §2.1); adopting real GIS data would be a scope change with no clear product benefit, since the city represents organizational structure, not geography |
| E. Generated from uploaded satellite imagery | Real-world imagery as a backdrop | **Not recommended**, same reasoning as D, plus real licensing/cost overhead for no confirmed product need |
| F. Generated dynamically from platform metadata | Layout derived from real `platform_registry`/module catalog (Sprint 34.2B) | Strongest long-term fit — the real Platform Registry already knows every module, vertical, and its visibility per client; a city that renders itself from this registry never drifts out of sync with what the platform actually offers |

### Recommendation: B + C + F combined, not a single option

- **F (platform metadata) generates the district skeleton** — every real module/vertical in the
  Platform Registry gets a real district automatically, closing the coverage gap in §3 permanently, not
  as a one-time fix.
- **B (company structure) generates the per-company internal layout** once a company is large enough to
  need its own sub-map (the "district-of-districts" tier in §2).
- **C (CRM relationships) generates the inter-company graph** for Partner Portal / cross-org views.
- **A (hand-crafted) remains the right choice only for the single reference city's aesthetic
  polish** — the Odessa reference city's specific visual character, not its structural layout, which
  should still come from F.

This combination means the city **never goes structurally stale** — a new vertical registered in the
real Platform Registry automatically has a place in the city, closing the §3 gap as a standing property
of the architecture, not a one-time content addition.

## Non-goals

- No real GIS/satellite integration — explicitly declined, per D/E's assessment.
- No manual per-company city design at scale — B/C/F's generative approach is required past the
  single-company tier.

## Related documents

`docs/ENTERPRISE_CITY_2D_VISION.md`/`docs/ENTERPRISE_CITY_UX_ARCHITECTURE.md`/`docs/ENTERPRISE_CITY_
RENDERING_ARCHITECTURE.md` (companions), `docs/CROSS_VERTICAL_EXTENSIONS.md` (CQ-19, the `module`
pattern), `docs/UNIFIED_PLATFORM_REGISTRY_34_2B.md` (real, the Option F data source), `docs/EBN_
BUSINESS_GRAPH.md` (CQ-10, the Option C data source), `docs/CITIZEN_ORGANIZATION_MEMBERSHIP.md`
(CQ-12, the Option B data source), `docs/CITY_LIVING_ECONOMY.md` §2.1 (CQ-10, why D/E are declined).
