# Enterprise City 2D — Vision Document

**Role:** Lead UX Architect & Digital Twin Architect. Documentation only, no code written, no existing
module rewritten.

## 1. What Enterprise City is, restated correctly

Enterprise City is not a game and not a decorative dashboard skin. It is the platform's **visual
operating system** — the spatial layer that makes an otherwise abstract collection of modules (CRM,
ERP, Knowledge Base, AI Agents, a dozen verticals, executive tooling) navigable the way a human
actually thinks about an organization: as places, not menu items. A district is not a theme; it is a
real destination with real state behind it. This document does not propose a new metaphor — the
metaphor is correct and already partially real. It proposes fixing the two things standing between the
current prototype and a production-grade visual OS: **the rendering substrate** and **the coverage
gap between the city's districts and the platform's real verticals**.

## 2. Current situation, verified precisely (not assumed)

Direct inspection this pass confirms the brief's own diagnosis, with exact root causes:

- **Rendering is 100% DOM/CSS.** Every building and district in the real implementation
  (`EnterpriseCityPage.tsx`) is an absolutely-positioned `<div>` with `style={{ left: x+'%', top:
  y+'%' }}`. Zero `<canvas>` elements, zero WebGL, zero PixiJS/Konva/Fabric/React-Flow/Leaflet/
  OpenLayers anywhere in `src/web/package.json`'s real dependency list. This is the precise, verifiable
  root cause of "rendering is unreliable" — a DOM tree of many absolutely-positioned elements does not
  batch draw calls, forces layout recalculation on pan/zoom, and has no GPU-accelerated sprite path.
  This is not a bug to patch; it is the wrong substrate for the stated goal, and this document's
  rendering-architecture companion (`ENTERPRISE_CITY_RENDERING_ARCHITECTURE.md`) recommends the fix.
- **District coverage has not kept pace with real platform breadth.** The real Sprint 30.4 "full Beta
  district set" has 16 districts (CRM, ERP, Finance, Production Studio, Warehouse, Legal, Marketing,
  AI Center, Security, Analytics, Documents, Marketplace, Knowledge Center, Developer Zone,
  Administration, Production/Manufacturing). **None of the brief's named verticals with real backend
  implementations — Crypto OTC (`crypto_enterprise`), Drone Engineering (`drone_platform`), Agro
  Trading (`agro_enterprise`), Cafe & Beauty — have a dedicated district today.** This is the precise,
  verifiable root cause of "navigation is incomplete" — real platform capability exists with no place
  in the city to stand on.
- **The good news, stated plainly**: the coordinate model, district/building data shape, and real Life
  Engine event-driven "what's happening right now" pipeline (`DAILY_OPERATIONS_MODEL.md`, real Sprint
  29.2) are sound. This is not a redesign of *what* the city represents — it is a redesign of *how it's
  drawn* and an *expansion of what it covers*.

## 3. Design principles for the next Enterprise City

1. **A building is never decoration.** Every visual element traces to a real platform fact — this
   engagement's own long-standing discipline (`docs/CITY_LIVING_ECONOMY.md`, CQ-10), restated as the
   non-negotiable design constraint for this redesign specifically.
2. **The city is the map, not the territory.** It visualizes real state; it does not become a second
   source of truth for anything. Every district's content is a read projection of a real
   platform_*/applications/* system, never new business logic.
3. **Nothing disappears, only re-renders.** A dormant vertical's building shrinks or dims; it is never
   removed. Consistent with this engagement's established principle, now extended explicitly to new
   verticals as they're added.
4. **Role determines visibility, not existence.** The same city exists for every user; what renders
   differs by real permission scope (`docs/DIGITAL_TWIN_STANDARDS.md` §3's composed Visibility model) —
   never a second city per role.
5. **2D first, engineered for 3D/AR/VR later without a rewrite.** The rendering architecture
   recommendation is chosen specifically because it doesn't foreclose that path — detailed in
   `ENTERPRISE_CITY_RENDERING_ARCHITECTURE.md` §5.

## 4. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| A rendering-engine migration is treated as a rewrite of the whole City, not a substrate swap | High | Keep the real data layer (`cityCatalog.ts`, `cityDistricts.ts`, Spatial Runtime) unchanged; only the render target changes — detailed in the rendering-architecture companion |
| New districts are added faster than the verticals behind them are real | Medium | Apply this document's own Principle 1 — a district for a thin/SPEC vertical (per `docs/ENTERPRISE_SCENARIO_LIBRARY.md`'s CQ-17 real-vs-SPEC scorecard) should visually communicate that honestly, not imply parity with a mature district |
| Scaling the district/building count to "thousands of companies" (per the brief) is attempted by literally rendering thousands of buildings at once | High | LOD and clustering are load-bearing requirements, not polish — detailed in Information Architecture §5 (scaling model) |
| The migration stalls mid-way, leaving two rendering paths (old DOM, new engine) both live | Medium | Sequence as a phased roadmap with each phase shippable independently — see `ENTERPRISE_CITY_2D_ROADMAP.md` |
| 3D/AR/VR ambition pulls investment away from finishing the 2D product | Medium | Per `CLAUDE.md`'s own standing sequencing rule ("Enterprise City is sequenced after platform completion") — this document does not recommend starting 3D/AR/VR work now, only choosing a 2D architecture that doesn't block it later |

## 5. Enterprise readiness score

**42 / 100** for the current implementation as a production-ready visual operating system — not a
verdict on the concept (which this document endorses), but on the current substrate and coverage.
Scoring basis: rendering substrate (0/25 — DOM-based, not viable at the brief's stated scale targets),
information architecture (14/25 — real, sound data model, real district/building shape, but missing
coverage for most named verticals), interaction completeness (10/25 — real pan/zoom/select/breadcrumb/
favorites exist per `docs/CITY_NAVIGATION_GUIDE.md`, no multi-select/context-menu/mini-map per
`docs/CITY_NAVIGATION.md` CQ-30.1 findings), live-data integration (18/25 — the real Life Engine event
bridge is genuinely strong and directly reusable, the strongest single asset this review found).

## Related documents

`docs/ENTERPRISE_CITY_UX_ARCHITECTURE.md`, `docs/ENTERPRISE_CITY_INFORMATION_ARCHITECTURE.md`,
`docs/ENTERPRISE_CITY_RENDERING_ARCHITECTURE.md`, `docs/ENTERPRISE_CITY_2D_ROADMAP.md` (this
document's five companions), `docs/CITY_LIVING_ECONOMY.md` (CQ-10, the real-fact discipline), `docs/
DAILY_OPERATIONS_MODEL.md` (CQ-17, real Life Engine), `docs/ENTERPRISE_SCENARIO_LIBRARY.md` (CQ-17,
real-vs-SPEC vertical scorecard), `CLAUDE.md` (City-after-platform sequencing rule).
