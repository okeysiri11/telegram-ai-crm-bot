# Enterprise City 2D — Rendering Architecture & Technology Comparison

**Role:** Lead UX Architect & Digital Twin Architect. Documentation only, no code written, no
technology adopted in this pass — recommendation only.

## 1. Why this matters more than any other decision in this redesign

Confirmed this review (`docs/ENTERPRISE_CITY_2D_VISION.md` §2): the current implementation renders
every building and district as an absolutely-positioned DOM `<div>`. This is the single root cause of
"rendering is unreliable" at the brief's stated scale targets — DOM reflow cost scales badly with
element count, CSS-transform pan/zoom on a deep div tree is not GPU-batched, and there is no sprite-
atlas/draw-call-batching path available to a pure-DOM approach. Every other decision in this document
set is secondary to getting this one right.

## 2. Technology comparison

| Technology | Rendering model | Strength for this use case | Weakness for this use case |
|---|---|---|---|
| **Current (DOM/CSS)** | HTML elements, absolute positioning | Zero new dependency, real accessibility for free (real DOM nodes), simple React integration | Confirmed root cause of the instability this document exists to fix; does not scale past low hundreds of simultaneously-rendered elements without jank |
| **PixiJS** | WebGL (Canvas 2D fallback), sprite-batched | Purpose-built for exactly this shape of problem (many 2D sprites, real-time updates, smooth pan/zoom, proven at scale in production 2D games/city-builders); real texture atlasing and draw-call batching | Imperative API, needs a bridge library for React (`@pixi/react`) or manual lifecycle management; no built-in accessibility — interactive elements need a parallel real-DOM layer for screen readers |
| **Konva (react-konva)** | Canvas 2D, retained-mode scene graph | Much more React-native feel than raw PixiJS, good shape/group/layer model, easier learning curve | Canvas 2D is CPU-bound, not GPU-batched like WebGL — will hit a real ceiling well before PixiJS at "thousands of companies" scale |
| **React Flow** | DOM/SVG, CSS-transform positioned nodes | Excellent for node-graph-shaped views specifically (Partner Portal's cross-org relationship graph), real built-in pan/zoom/minimap/multi-select out of the box | Same fundamental DOM-positioning approach as the current implementation for the *node* rendering — does not solve the core scaling problem for a "world map with many small buildings" view; right tool for a different shape of view (see §3) |
| **Leaflet** | Tile-based, real geo-coordinate assumptions | Mature, huge plugin ecosystem, real clustering support proven at scale for real map data | Built around real lat/lng — this engagement's own CQ-10 research already found the city is deliberately *not* real-GIS-backed; fighting a geo-centric library to represent an abstract organizational space is the wrong tool for the wrong problem |
| **OpenLayers** | Tile-based, more powerful/complex than Leaflet | Same real strengths as Leaflet, more configurable | Same mismatch as Leaflet, plus steeper learning curve for no corresponding benefit given this city isn't real-GIS-backed |
| **Tiled (map editor) + tilemap rendering** | Grid-tile-based authoring + a tile renderer (commonly paired with PixiJS/Phaser) | Good *authoring* tool for a designer laying out the reference Odessa-styled city's static terrain/roads — a real, mature open-source tool | Not a fit as the *runtime* interaction model — a business district isn't naturally tile-grid-shaped the way a game level is; recommend as an authoring aid only, not a runtime dependency |
| **Custom infinite-canvas engine (à la Figma/tldraw)** | Custom WebGL/Canvas | Maximum control | High build/maintenance cost for a capability PixiJS already provides — not recommended; reinventing this is not a good use of engineering effort at this stage |

## 3. Recommendation: PixiJS as primary renderer, React Flow for one specific secondary view, real DOM for accessibility and UI chrome

**Primary city view (districts, buildings, movement, live indicators): PixiJS**, wrapped via `@pixi/
react` for React integration. This directly targets the confirmed root cause in §1 and is the only
option in the comparison table purpose-built for "many 2D sprites, real-time, smooth pan/zoom, scales
to thousands" — the brief's own stated requirement.

**Partner Portal / cross-org relationship graph specifically: React Flow**, not PixiJS. This is a
different visual *shape* of problem — a node graph with edges representing real `Relationship` data
(`EBN_BUSINESS_GRAPH.md`, CQ-10), not a spatial world map. React Flow's real built-in graph-navigation
primitives (minimap, multi-select, auto-layout) are the right fit for this one view specifically. This
is a deliberate two-renderer decision, not indecision — each renderer is scoped to the view shape it's
actually good at, and neither view needs the other's capabilities.

**Accessibility and UI chrome (info panels, context menus, search, command palette): real DOM,
unchanged.** PixiJS's canvas has no native accessibility tree — every interactive city element needs a
corresponding real, hidden-but-focusable DOM element (a standard, well-understood pattern for
canvas-based applications, not a novel problem this document needs to solve from scratch) so screen
readers and keyboard navigation continue to work. This is a real engineering requirement of the
recommendation, not an afterthought.

## 4. Open-source projects worth studying (not adopting wholesale)

| Project | Why it's relevant |
|---|---|
| **Phaser** | A mature open-source game framework built on a PixiJS-like renderer — worth studying its scene-management and camera-system design even though this document does not recommend adopting a full game framework (unnecessary overhead for a business application) |
| **deck.gl** | WebGL-based large-scale data visualization (points, clusters, aggregation layers) — directly relevant reference for §5's "thousands of companies" clustering/LOD requirement, since this is exactly the problem deck.gl solves for geospatial data at scale |
| **tldraw** (open-source infinite canvas) | Excellent reference for pan/zoom/selection/multi-select interaction UX patterns, even though it's SVG/Canvas-based for a different use case (whiteboarding) — worth studying its interaction code, not adopting its rendering approach |
| **react-zoom-pan-pinch** | A lightweight, focused pan/zoom/pinch utility — worth evaluating as a smaller-footprint alternative to building custom camera controls on top of PixiJS's own transform system |
| **Tiled Map Editor** | Recommended as an authoring tool for the reference Odessa-styled city's static layout (§2), not a runtime dependency |
| **OpenRCT2** (open-source city/park simulation) | Research-only reference for "how does a mature 2D simulation handle thousands of visible agents with smooth performance" — a pattern-study source, not a code dependency; its entity-culling and update-batching approach is directly relevant to §5 below |

## 5. Migration approach — substrate swap, not a rewrite

Per `docs/ENTERPRISE_CITY_2D_VISION.md`'s Risk table: the real data layer (`cityCatalog.ts`,
`cityDistricts.ts`, Spatial Runtime, the Life Engine event bridge) does not change. Only the render
target changes — from "map real data to DOM `style` props" to "map real data to PixiJS sprite
properties." This is architecturally a swap of the last mile, not a redesign of the ~15 real
subsystems (Spatial Runtime, Life Engine, Business Network, etc.) that feed the city. Sequencing detail
is in `ENTERPRISE_CITY_2D_ROADMAP.md`.

## 6. Future evolution: 3D, Digital Twin, AR, VR, Spatial Computing — without rewriting the 2D engine

This is the direct payoff of choosing a WebGL-based renderer (PixiJS) over a DOM-based or Canvas-2D-
based one now: **WebGL and WebGL-based 3D (Three.js, Babylon.js) share the same underlying GPU
programming model** — the mental model of "sprites/meshes, camera, transforms, batched draw calls"
carries forward directly, unlike a jump from DOM or Canvas 2D to 3D, which would be a much larger
conceptual leap.

The concrete evolution path, none of which requires touching the real data layer:

1. **2D (this document's recommendation)** — PixiJS renders the real `SpatialEntity` hierarchy as flat
   sprites.
2. **2.5D / Digital Twin visual upgrade** — the same real data, rendered with isometric or pseudo-depth
   sprites in PixiJS itself (no new engine needed) — a purely visual upgrade.
3. **3D** — a Three.js (or Babylon.js) renderer consuming the *same* real `SpatialEntity`/Life Engine
   data the 2D renderer consumes, added as a second render target the way React Flow is added as a
   second view in §3 — the real coordinate data (`GeoLocation`, `planeToGeo()`, CQ-16) already carries
   `lat`/`lng` fields that translate directly into a 3D world-space position.
4. **AR** — a WebXR-based renderer, again consuming the same real data, appropriate once a real mobile/
   wearable client exists (currently unbuilt per every prior review in this engagement).
5. **VR / Spatial Computing** — the furthest-out step, same principle: a new render target, same real
   data contract, no earlier layer touched.

**The one design discipline that makes this whole path real, not aspirational**: the recommendation in
§3 already separates "what the city is" (real data) from "how it's drawn" (the renderer) — this is not
a new principle invented for the 3D future, it's the same principle chosen for entirely present-day
reasons (fixing the DOM performance problem) that happens to also be exactly what a rewrite-free 3D
path requires.

## Non-goals

- No 3D/AR/VR work scheduled or recommended to start now — per `CLAUDE.md`'s own City-after-platform
  sequencing rule, restated.
- No custom rendering engine built from scratch — PixiJS is mature, real, and sufficient.
- No adoption of Leaflet/OpenLayers/real GIS — declined per `ENTERPRISE_CITY_INFORMATION_
  ARCHITECTURE.md` §4's Option D/E assessment.

## Related documents

`docs/ENTERPRISE_CITY_2D_VISION.md`/`docs/ENTERPRISE_CITY_INFORMATION_ARCHITECTURE.md`/`docs/
ENTERPRISE_CITY_2D_ROADMAP.md` (companions), `docs/REGIONAL_DIGITAL_TWIN.md` (CQ-16, real `GeoLocation`/
`planeToGeo()` — the coordinate data this document's §6 evolution path relies on), `docs/CITY_
SIMULATION.md` (CG-4/CG-9, the real performance-budget discipline this recommendation extends).
