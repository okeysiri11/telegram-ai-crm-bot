# Enterprise City 2D — Implementation Roadmap & Scalability Design

**Role:** Lead UX Architect & Digital Twin Architect. Documentation only, no code written.

## 1. Scalability design, by the brief's explicit tiers

| Tier | Design |
|---|---|
| 10 users | No special handling needed — current real data layer + new PixiJS renderer both comfortably sufficient |
| 100 users | Same — the bottleneck at this tier is concurrent-session server load (a backend concern, `docs/SCALABILITY_REVIEW.md`), not city rendering |
| 1,000 users | Renderer unaffected (rendering cost is a function of visible *entities*, not connected *users*); real-time update fan-out via the Life Engine event bridge should be checked for per-session filtering so 1,000 users aren't each receiving every other user's raw event stream unfiltered |
| 10,000 users | Same rendering answer; this is where the real backend's per-tenant queue/event-bus scaling (`docs/ARCHITECTURE_REVIEW_34_2C.md` §7/§9) becomes the binding constraint, not the city itself |
| 100 companies | The "district-of-districts" clustering tier (`ENTERPRISE_CITY_INFORMATION_ARCHITECTURE.md` §2) activates — PixiJS's real sprite-batching handles this comfortably |
| 1,000 companies | Full LOD/clustering discipline required — aggregate markers only, drill-down on selection, per the same document's §2 "thousands of companies" tier |
| Millions of CRM records | **Never rendered as individual city objects** — a CRM entity (a `Deal`) renders as an aggregate position on a pipeline road (§1 of the Information Architecture doc) or a cluster marker, never one sprite per record; the real backend's own data-volume handling (partitioning, per `docs/ARCHITECTURE_REVIEW_34_2C.md` §6) is the actual scaling answer for the *data*, the city only ever renders a bounded, LOD-appropriate *view* of it |

**The governing principle across every tier**: the city's rendering cost must be a function of what's
**visible on screen at the current zoom level**, never a function of total platform data volume — the
same discipline the real Graphics Engine already established for a single city (`docs/CITY_
SIMULATION.md`, CG-4/CG-9), extended explicitly to multi-company and multi-million-record scale.

## 2. Implementation complexity estimates

| Work item | Complexity | Why |
|---|---|---|
| PixiJS renderer replacing the DOM renderer, same real data contract | L | Substantial but bounded — a substrate swap, not new data modeling (per the Rendering Architecture doc §5) |
| Real-DOM accessibility overlay for the PixiJS canvas | M | Well-understood pattern, not novel engineering |
| Mini-map | S | Small, self-contained addition |
| Multi-selection + batch context actions | M | New interaction, moderate scope |
| Six new districts (Crypto, Drone, Agro, Cafe & Beauty, Partner Portal, + SPEC placeholders) | M | Mostly data/catalog work, reusing the real `module` pattern |
| District-of-districts clustering (100-company tier) | L | New rendering behavior, real underlying data hierarchy already exists |
| Full LOD/aggregate-marker clustering (1,000+-company tier) | XL | The single largest engineering item in this roadmap — genuinely new capability |
| React Flow-based Partner Portal relationship graph | M | Self-contained, real underlying `Relationship` data already exists |
| Drone/Crypto live-data bridges into the Life Engine event stream | M each | New integration work, not a redesign — real event bridge pattern already established |
| Option F (platform-metadata-driven district generation) | L | New generative layer over the real Platform Registry |

## 3. Suggested Sprint roadmap, from 35.1 onward

**Phase 1 — Substrate (35.1–35.3)**
- 35.1: PixiJS integration proof-of-concept — render the existing real 16-district, 44-building
  dataset through PixiJS instead of DOM, feature-flagged alongside the current implementation (not a
  cutover yet).
- 35.2: Accessibility overlay + interaction parity (pan/zoom/select/breadcrumb/favorites) with the
  current real implementation — no regressions.
- 35.3: Cutover — PixiJS becomes the default renderer; retire the DOM renderer once parity is proven.

**Phase 2 — Coverage (35.4–35.6)**
- 35.4: New districts for Crypto OTC, Drone Engineering, Agro Trading (real backends, highest-value
  gap per this review's Information Architecture findings).
- 35.5: New districts for Cafe & Beauty, Partner Portal; SPEC-placeholder districts for Medical/
  Construction/Manufacturing, honestly labeled as thin per this document's own vision principles.
- 35.6: Live-data bridges for Drone missions and Crypto deals into the real Life Engine event stream.

**Phase 3 — Interaction depth (35.7–35.8)**
- 35.7: Mini-map, multi-selection, batch context actions.
- 35.8: React Flow-based Partner Portal relationship graph.

**Phase 4 — Scale (35.9–36.1)**
- 35.9: District-of-districts clustering (100-company tier).
- 36.0: Full LOD/aggregate-marker clustering (1,000+-company tier) — the roadmap's largest single item,
  given its own dedicated sprint deliberately.
- 36.1: Option F — platform-metadata-driven district generation, closing the coverage gap permanently
  as a standing architectural property rather than a one-time content pass.

**Phase 5 — Future (unscheduled, demand-driven)**
- 3D/Digital Twin visual upgrade, AR, VR — per the Rendering Architecture doc §6, only once the 2D
  product is complete and platform completion allows City investment per `CLAUDE.md`'s own sequencing
  rule.

## 4. Risks (roadmap-specific, complementing the Vision document's risk table)

| Risk | Mitigation |
|---|---|
| Phase 1's feature-flagged parallel-renderer period runs indefinitely instead of cutting over | Set an explicit cutover gate (35.3) with a defined parity checklist, not an open-ended "when ready" |
| Phase 2's new districts get built before Phase 1's renderer is stable, doubling migration surface | Sequence strictly — no new district content on the old DOM renderer once Phase 1 begins |
| Phase 4's clustering work is deferred indefinitely because it's the hardest item | Give it its own dedicated sprint (36.0) rather than folding it into a "polish" sprint where it would compete with easier, more visible work |

## 5. Enterprise readiness — path to a high score

Restated from the Vision document's current **42/100**: this roadmap, fully executed through Phase 4,
directly addresses every scoring gap identified there — rendering substrate (Phase 1), information
architecture coverage (Phase 2), interaction completeness (Phase 3), and the scale requirement the
brief explicitly asked for (Phase 4). Live-data integration, already the strongest current score
(18/25), improves further via Phase 2's new bridges. A realistic post-Phase-4 re-assessment would be
expected in the 80-85/100 range, contingent on execution quality, not a design gap this roadmap leaves
unaddressed.

## Related documents

`docs/ENTERPRISE_CITY_2D_VISION.md` (the 42/100 baseline this roadmap improves on), `docs/ENTERPRISE_
CITY_UX_ARCHITECTURE.md`/`docs/ENTERPRISE_CITY_INFORMATION_ARCHITECTURE.md`/`docs/ENTERPRISE_CITY_
RENDERING_ARCHITECTURE.md` (the design decisions this roadmap sequences), `docs/ARCHITECTURE_REVIEW_
34_2C.md` (the platform-wide scalability findings this roadmap's §1 defers to for backend concerns),
`CLAUDE.md` (City-after-platform sequencing rule, governing Phase 5).
