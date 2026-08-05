# Enterprise City — Complete Product Design Specification

**Status:** permanent product bible chapter. Documentation only — no implementation in this document,
no code referenced here should be modified as a result of reading it. **The City is not a game.** It
is the visual representation of the Enterprise Platform: a spatial map where every building is a real
business module, every state reflects live platform data, and every entry point leads to a real,
existing destination. A building that looks busy *is* busy — its visual state is derived from the same
signals that drive the Dashboard, never from decoration.

**Version lineage:** City Experience `1.1` (`CITY_EXPERIENCE_VERSION`, EP-05 + Sprint 27.8 Core)
built on Sprint 32.3.3's original `/enterprise-city` 2D navigation concept — both are the
**shipped, real** foundation this document builds forward from. Sprint 27.8 elevates City to the
primary navigation space over Enterprise Desktop (see `ENTERPRISE_CITY_CORE.md`, `CITY_ENGINE.md`,
`CITY_DISTRICTS.md`).

**Implementation reference (2D, shipped):** `src/web/src/enterprise-city/` (`cityCatalog.ts`,
`cityDistricts.ts`, `cityEngine.ts`, `cityNavigation.ts`, `cityVisualLanguage.ts`,
`EnterpriseCityPage.tsx`, `useCityLiveStatus.ts`) + `src/web/src/index.css`
(`.ec-*` classes) + `src/web/design-system/styles/motion.css`. Routes: `/enterprise-city`, `/city`.
Desktop opens City via `/enterprise-city?embed=1`. The City
follows `ENTERPRISE_DESIGN_SYSTEM.md` in full — typography, color, spacing, motion, and glass-chrome
rules are inherited, never reinvented, in both modes described below.

**Naming note:** `docs/SMART_CITY.md` (`applications/auto_marketplace/mobility_platform/`) is an
unrelated automotive vertical feature — literal city infrastructure APIs (parking, traffic, road
sensors) for the auto marketplace product. No relationship to the Enterprise City described here.

---

## 1. Vision

Enterprise City is the platform's answer to a simple problem: **an enterprise is not a list, it is a
place.** A CRM, a Finance department, an AI team, a marketplace — in every other view of this platform
these are rows in a menu or cards in a dashboard. In the City, they are buildings a person can walk
into. The vision is that opening the City should feel less like opening a dashboard and more like
looking out over a city from a rooftop: you see the whole operation, you notice what's glowing and
what's quiet, and you decide where to go next — the same instinct a founder has walking their own
factory floor, scaled to however large the enterprise has grown.

The long-range vision (beyond today's 2D shipped experience, see §7) is a City that scales its own
visual complexity to match the complexity of the organization it represents — from a single small
building for a five-person company, to a skyline for a holding company, to a fully explorable
three-dimensional metropolis for an international enterprise or a government instance (§23). The City
is designed to **grow with the business**, never to be re-designed for it.

---

## 2. Philosophy

1. **The City is a rendering, not a system.** It holds no engine, store, runtime, or AI core of its
   own (an explicit architecture-compliance constraint carried since Sprint 32.3.3 and reaffirmed in
   EP-05, and preserved unchanged as this document extends the concept into 3D). It is presentation
   over data and routes that already exist elsewhere in the platform. If a future idea for the City
   requires new backend state, that idea belongs to the system it's actually about, with the City only
   visualizing the result.
2. **State of the business at a glance.** A city that looks calm should mean the business is calm; a
   building glowing amber should mean something in that module genuinely needs attention right now.
3. **Every building is a real destination.** The City never leads somewhere that doesn't already exist
   as a first-class page or capability — it is an alternative *entry point*, not a parallel product.
4. **Legible without reading.** Buildings carry distinct shape and silhouette so a returning user
   recognizes "that's Finance" before reading any label — the same "recognizable without a logo"
   instinct that governs the whole design system.
5. **Calm, meaningful motion only.** Focus-breathe, state-change flash, and an AI-activity pulse are
   the only sanctioned ambient motions in 2D; the same discipline governs 3D camera and agent movement
   (§19) — nothing moves in the City "for delight" alone.
6. **A companion to the Dashboard, never a replacement.** A user can ignore the City entirely and lose
   no capability (§4).
7. **Executive tone carries into the City.** AI hints inside the City follow the same
   Observation → Why → Action → Impact structure and calm advisor voice defined in
   `ENTERPRISE_DESIGN_SYSTEM.md` §16.
8. **One city, one truth.** Whichever mode a user is in — 2D or 3D — the underlying building catalog,
   live status, and routes are identical. Mode is a rendering choice, not a different product with
   different data (§7).

---

## 3. Why Enterprise City exists

Three concrete gaps the City fills that the Dashboard and Workspace do not:

1. **Spatial memory beats list memory.** People remember *places* better than they remember *menu
   items* — "the AI district is over on the right, past Analytics" is a durable mental model in a way
   "item 14 in the sidebar" is not. The City exists to give the platform a mental map, not just a menu.
2. **The whole organization, visible at once.** No dashboard widget shows fifteen-plus modules'
   simultaneous health in one glance the way a city skyline does — the City is the platform's single
   widest-angle view.
3. **Process made visible in space.** A workflow route line crossing the map (§21) shows a business
   process moving through the organization in a way no list-based workflow viewer can — this is the
   City's most genuinely unique value versus every other surface in the platform.

The City deliberately does **not** exist to be a new navigation engine, a new dashboard, or a new
workflow engine — see §4–§6 for how it relates to (and stays a thin layer over) each of those.

---

## 4. Relationship with Dashboard

- **Dashboard is the morning briefing; the City is the walkthrough.** Per `ENTERPRISE_DESIGN_SYSTEM.md`
  §14, the Dashboard's job is ~10-second comprehension via the Executive Morning Brief. The City's job
  is spatial exploration once that brief has told you *where* to look.
- **Shared data, not shared UI.** Both read from the same live-enterprise snapshot and notification
  signals — a building glowing amber in the City and a card flagged in the Dashboard's "Needs
  attention" column are describing the same underlying fact, never two different computations of it.
- **The City's header always offers a one-click path back to Dashboard** (§20's context strip,
  "Decide on Dashboard") — the two are companions in the same decision flow, not competing home
  screens. Neither replaces the other; a user who never opens the City loses nothing, and a user who
  lives in the City can always return to the Brief.

---

## 5. Relationship with Workspace

- **Workspace is where work happens; the City is where work is found.** Clicking any building
  navigates into the real Workspace surface for that module (§9) — the City does not duplicate
  Workspace's dashboards, widgets, or personalization (`ENTERPRISE_DESIGN_SYSTEM.md` §15); it is
  purely the spatial index pointing into Workspace.
- **Workspace's per-tenant vertical enablement is the City's building visibility source of truth**
  (§13, §23) — a tenant without the Agro vertical enabled sees no Agro building, exactly as they'd see
  no Agro entry in Workspace navigation. The City never maintains its own separate enablement list.
- **The City is optional, Workspace is not.** Every capability reachable from the City is also reachable
  from Workspace/global navigation directly — the City adds a spatial lens on top, it is never the
  sole path to a capability.

---

## 6. Relationship with AI Agents

- **AI presence is a status signal on real buildings, not a wandering character (2D).** The AI dot
  (§19) appears on any building currently being worked on by an agent — this is how the 2D City shows
  AI "visiting" a module without a moving sprite.
- **In 3D (§7.2, Vision), AI agents may be represented as small, purposeful moving markers** traveling
  between buildings along the same workflow-route lines a business process uses (§21) — this is the
  one exception to "no traveling objects" (§2.5), because an agent genuinely *is* moving work from one
  module to another; the motion is a truthful visualization of a real orchestration event
  (`platform_orchestrator`/`platform_agents`), not decoration. It must still obey the calm-motion rule:
  steady, deliberate movement between two real points, never a looping or idle animation.
- **The City's AI voice is the platform's one Executive Advisor persona** (`ENTERPRISE_DESIGN_SYSTEM.md`
  §16) in every mode — there is no City-specific AI character, in 2D or in the 3D vision.

---

## 7. Two modes: 2D and 3D

The City has one data model and two renderings. A user (or tenant policy) chooses a mode; nothing about
the underlying building catalog, live status, or routing changes between them.

### 7.1 2D mode — **Shipped**

The real, running experience today: a flat, DOM/CSS map (no WebGL/canvas), buildings as absolutely-
positioned tiles on a percentage-based plane, silhouettes as CSS shapes, viewport pan/zoom as a CSS
transform. Full detail in §§9–22 below (all sections marked **Shipped** describe this mode
specifically). Chosen deliberately for low GPU cost, fast load, and accessibility (§19) — this is not
a "placeholder until 3D ships," it is the platform's primary, permanent mode for most tenants,
especially smaller ones (§23).

### 7.2 3D mode — **Vision (not implemented)**

A designed future rendering of the identical building catalog as a navigable three-dimensional
environment. 3D mode exists for organizations large enough that a flat map's legibility starts to
strain (§23's Holding/International/Government/Ecosystem tiers) — it is an alternative *view*, not a
richer product; a building in 3D mode has exactly the same identity, route, and live-status meaning as
its 2D counterpart.

**What changes in 3D:**
- Buildings become volumetric forms (§9's district shape language extends from 2D `border-radius`
  values into real building *massing* — Commerce district buildings are low and wide with soft
  corners; Ops district buildings are tall, angular, mechanical; Intel district buildings are
  asymmetric towers).
- The camera becomes a real free/orbit camera instead of a 2D transform (§18).
- Zoom becomes discrete levels with genuinely different content density per level (§14), not one
  continuous scale.
- Transportation gains literal, minimal transit visualizations along workflow routes (§13, §6).
- Districts, Departments, Enterprises, and Portals (§9–§12) become spatially distinguishable at
  different zoom levels rather than only visually distinguishable at one flat zoom.

**What never changes in 3D:** the "no new engine" rule (§2.1), the "every building is a real
destination" rule (§2.3), the calm-motion discipline (§2.5, §19), and the fact that clicking/selecting
a building still simply navigates to its real route. 3D is a richer *lens*, never a richer *product* —
it must not require new backend capability beyond what 2D already visualizes; if a 3D idea seems to
need new data, that idea belongs to the system it's actually about (§2.1), exactly as in 2D.

**Mode switching** is a per-user or per-tenant preference, not a one-way migration — a user can switch
between 2D and 3D at any time and land in the same focused building/workflow context they left, since
both modes render the same underlying focus/viewport state (§17's session-scoped focus applies to
either mode identically).

---

## 8. Districts

**Shipped (2D).** Buildings are grouped into five districts, each with its own **shape language**
expressed through `border-radius` on the building tile — the district is legible from silhouette
alone, before any color or label:

| District | Shape language (2D) | `border-radius` | Character | Current buildings |
|---|---|---|---|---|
| **Commerce** | Softly rounded, approachable | `0.65rem` | Revenue-facing, customer-facing | CRM, Sales, Marketing, Finance |
| **Ops** | Sharp, mechanical | `0.35rem` | Execution, production, live operations | Production, Mission Control |
| **People** | Very rounded, organic | `1.1rem` | Human-centered | HR, Administration |
| **Intel** | Asymmetric cut corner | `0.5rem 0.95rem` | Knowledge, cognition, analysis | Analytics, AI Team, Knowledge, Documents, Concierge |
| **Hub** | Bold 2px primary-tinted border | (default `--eds-radius-xl`) + heavy border | The center of the city — always visually anchored | Enterprise Hub, Command Center (Dashboard) |

**Vision (3D):** the same five districts become real neighborhoods with distinct **massing language**
— Commerce as a low, dense retail-street silhouette; Ops as tall angular industrial forms; People as
organic, park-adjacent low-rise; Intel as slender asymmetric towers clustered around a shared plaza;
Hub as the tallest, most central structure, visible from anywhere in the city as an orientation anchor
(the 3D equivalent of the 2D Hub's "always visually anchored" rule).

**Rules (both modes):**
- A district's shape/massing language applies uniformly to every building inside it.
- Districts have **soft link lines** connecting buildings within the same district (2D: dashed SVG at
  ground level; 3D vision: the same relationship rendered as a low, subtle ground-plane connector, not
  an elevated road — see §13) — these represent *organizational proximity*, never a literal transit path.
- Districts carry no separate RBAC/routing scope by themselves; role-awareness layers on top (§17).

---

## 9. Buildings — module map

### 9.1 Shipped today (15 buildings, `CITY_BUILDINGS` in `cityCatalog.ts`)

| Building | District | Route | Silhouette (2D) | Purpose |
|---|---|---|---|---|
| Enterprise Hub | Hub | `/workspace` | Circle (`ec-sil-hub`) | Center of the company |
| Command Center (Dashboard) | Hub | `/dashboard` | Flat rectangle outline (`ec-sil-dash`) | Command center |
| CRM Center | Commerce | `/workspace/crm` | Rounded rect, tall (`ec-sil-crm`) | Clients and deals |
| Sales | Commerce | `/workspace/crm` | Triangle/peak (`ec-sil-sales`) | Sales funnel |
| Marketing | Commerce | `/workspace` | Pill, flat base (`ec-sil-mkt`) | Growth and campaigns |
| Finance | Commerce | `/workspace/finance` | Rect with inset ledger bar (`ec-sil-fin`) | Finance |
| Production | Ops | `/workspace/drone` | Rotated diamond (`ec-sil-prod`) | Production/operations |
| Mission Control | Ops | `/platform-builder/mission-control` | Outlined square, offset ring (`ec-sil-mc`) | Live operations |
| HR | People | `/workspace/hr` | Circle with duplicate shadow (`ec-sil-hr`) | People |
| Administration | People | `/settings` | Rect, thick base (`ec-sil-admin`) | Administration |
| Analytics Center | Intel | `/platform-builder/intelligence` | Jagged skyline polygon (`ec-sil-bi`) | Analytics/KPI |
| AI Team Center | Intel | `/platform-builder/ai-team` | Double-ringed circle (`ec-sil-ai`) | AI agents/copilots |
| Knowledge Center | Intel | `/platform-builder/knowledge` | Thick left border (`ec-sil-kb`) | Knowledge base |
| Documents | Intel | `/workspace/docs` | Narrow tall rect (`ec-sil-docs`) | Files/documents |
| AI Concierge | Intel | `/platform-builder/concierge` | Ring, open top (`ec-sil-concierge`) | Executive Advisor |

Exact map coordinates, icon glyphs, and search tokens live in `cityCatalog.ts::CITY_BUILDINGS` — this
table is the human-readable summary, not a fork of it.

### 9.2 Designed extension — mapping the platform's remaining module surface

**Designed (2D extension).** The 15 shipped buildings cover the original Workspace/Platform-Builder
surface area; the platform has grown substantially since (`MODULES.md`, `API_MAP.md`). Each row below
is one proposed `CityBuilding` catalog entry, following the existing pattern exactly:

| Building | District | Maps to (real platform surface) | Proposed silhouette direction |
|---|---|---|---|
| **ERP Center** | Ops | `platform_management`/`platform_workflow` resource-planning surfaces, `applications/port_erp`, `applications/agro_marketplace` ERP modules | Grid/ledger silhouette, sharp Ops corners |
| **Marketplace Plaza** | Commerce | `applications/auto_marketplace`, `agro_marketplace`, `applications/marketplace` | Stall/arcade silhouette (repeated small arches) |
| **Automation Yard** | Ops | `platform_workflow`, `platform_workflows`, `platform_jobs`, `platform_tools` | Gear/conveyor silhouette |
| **AI Studio** | Intel | `platform_orchestrator`, `platform_agents`, `platform_reasoning`, `platform_planning`, `platform_decision` | Layered-ring silhouette — where agents are *built*, distinct from AI Team where they're *run* |
| **Security & Trust** | People | `platform_security`, `platform_identity`, RBAC/audit surfaces | Shield/keep silhouette, taller than Administration |
| **Communications Tower** | Commerce | `platform_communications_hub`, `platform_integrations` | Tall antenna/mast silhouette |
| **Observability Deck** | Ops | `platform_observability`, `platform_reliability` | Radar-dish silhouette, pairs with Mission Control |
| **Production Studio** *(if `AI_PRODUCTION_STUDIO.md` ships)* | Intel | `platform_production_studio/`, `applications/ai_production_studio/` | Camera-aperture silhouette (concentric rings, open center) |

**Rule for all future buildings, shipped or proposed:** a new building must map to one real, already
navigable route — the City visualizes what exists; it never gets ahead of the platform.

---

## 10. Departments

**Designed (both modes).** A department is a **sub-unit inside one building**, not a separate building
— the mechanism that lets a single City building represent a module with real internal structure
without fragmenting the map:

- In **2D**, a department surfaces as an expanded detail inside the existing Inspector panel (§20) when
  a building is focused — e.g. focusing "Finance" can show department chips (Treasury / AP-AR /
  Reporting) each linking to their real sub-route, without adding new tiles to the map.
- In **3D (vision)**, a department can be a distinguishable **floor or wing** of a building's volume,
  visible when the camera is at Building zoom level (§14) — e.g. the Finance tower shows a visibly
  distinct top floor for "Executive Reporting" versus a lower floor for "Transactions," without
  changing the building's footprint on the district map.
- **Departments never get their own City-catalog entry, route, or district membership** — they are
  strictly a presentation refinement of one building's existing identity (§4, `ENTERPRISE_DESIGN_
  SYSTEM.md` §13's card-anatomy pattern, generalized to 3D volumes). This is the direct application of
  §22's "sub-buildings over district explosion" growth rule.

---

## 11. Enterprises

**Designed (both modes, load-bearing for §23's scaling model).** An "Enterprise" in City vocabulary is
**one complete city instance** — the full district/building layout for one legal or operational
entity. This concept only becomes visible once a tenant operates more than one:

- **A single-company tenant has exactly one Enterprise** — its city *is* the company (§23, tier 1).
- **A holding-company tenant has multiple Enterprises**, each a complete, independently-buildable city
  (its own districts, its own building set, scoped to that subsidiary's enabled verticals) — the
  holding's *own* view is a **city of cities**: a higher-altitude map where each Enterprise appears as
  one node/skyline-cluster rather than individual buildings (§14's Region zoom level, §23 tier 2).
- **Navigating into an Enterprise** from the holding view is the same interaction as navigating into a
  building from a district view — click/select → descend one level → see the next layer of detail
  (§17). This recursive "one level deeper" interaction is what lets the City scale from one building to
  a government-scale map without inventing a new interaction model at each tier (§23).
- **Cross-Enterprise comparison** (a holding executive comparing two subsidiaries' health at a glance)
  reuses the exact same visual-state language (§9's `ok/attention/critical/running/waiting/done`) at
  the Enterprise-node level as at the building level — an Enterprise node glows amber under the same
  rules a building tile does.

---

## 12. Portals

**Designed (both modes, primarily meaningful at Ecosystem scale, §23 tier 5).** A portal is a
**controlled gateway between city instances belonging to different organizations** — the mechanism
that lets an Ecosystem-scale deployment (a marketplace network, a supply chain, a government service
directory) show connections *between* separate enterprises' cities without merging them into one
city or leaking one organization's internal building layout into another's view.

- A portal renders as a distinctive gateway structure (2D: a distinct silhouette at the district
  boundary; 3D vision: a visible arch/threshold structure at the city's edge) rather than as a regular
  building — it visually signals "this leads to a different organization's city," which no other
  element in the City needs to communicate.
- **Portals carry their own access boundary.** Crossing a portal is subject to the same RBAC/tenant
  isolation the platform already enforces elsewhere (`platform_identity`, `MODULES.md`) — a portal
  never grants implicit visibility into the destination city beyond what the visitor's role/partnership
  agreement allows; what's visible across a portal (e.g. only shared marketplace/logistics buildings,
  never a partner's internal Finance building) is a permissions question the City visualizes, not one
  it decides.
- **Portals are how the City stays legible at Ecosystem scale.** Instead of one unbounded mega-city
  merging every participant, portals keep each organization's city intact and connect them explicitly
  and visibly — the City's answer to "how do you show a network of enterprises without them blurring
  into one incomprehensible map."

---

## 13. Transportation

**Shipped (2D):** the City does not model literal roads or vehicles. "Transportation" is the mechanism
by which attention moves through the city, not a metaphor of trucks or trains:

1. **Direct navigation (teleport)** — clicking a building immediately navigates to its real route. No
   simulated travel animation; the City respects that users want to *arrive*.
2. **Viewport pan** — selecting a building from the minimap smoothly pans the viewport to center it,
   without changing route.
3. **Workflow route lines** (§21) are the closest 2D comes to depicting movement: a bright dashed
   polyline through the buildings an active workflow touches.

**Vision (3D):** transportation becomes slightly more literal, still under the calm-motion rule (§2.5):

- **Camera "flight" between buildings** replaces instant teleport for in-city navigation — a brief,
  fast (still within Motion Design Language's timing budget, `ENTERPRISE_DESIGN_SYSTEM.md` §9),
  purposeful camera move from the current focus to the destination building, so a user retains spatial
  orientation ("I moved from Finance to CRM, they're adjacent") rather than jump-cutting. This is the
  3D equivalent of 2D's `panTo`, not a new travel simulation.
  - **A shortcut always exists to skip the flight** (an instant-cut toggle/keyboard modifier) for users
    who want teleport speed — the flight is a spatial-orientation aid, never a mandatory delay.
- **Agent transit markers** (§6) travel along workflow-route paths between buildings — the one
  sanctioned "traveling object," because it visualizes a real orchestration event.
- **Inter-Enterprise transit** (holding/international scale, §11) — moving from one Enterprise's city
  to another's (or crossing a Portal, §12) uses a distinct, longer "ascend → traverse → descend" camera
  arc, so a user always feels the difference between "moving within my company" and "moving between
  organizations."
- **No decorative traffic.** There is no ambient vehicle/pedestrian simulation anywhere in the City, in
  either mode — every moving element on the map represents a real navigation action or a real agent
  task, with no exception.

---

## 14. Zoom levels

**Shipped (2D):** zoom is a **continuous scale**, not discrete named modes — `viewport.zoom` ranges
from **0.75 to 1.4** in **0.1 increments**, default `1.0`. For design purposes this reads as three
informal bands (not enforced steps): **Overview** (0.75–0.9, most/all districts visible), **Default**
(1.0, landing zoom), **Focus** (1.1–1.4, paired with pan-to). This is intentionally narrow because the
2D map holds 15–~30 buildings at a fixed DOM size — extreme range isn't needed at that scale.

**Vision (3D):** zoom becomes **true discrete levels**, each with genuinely different content density —
this is the one place 3D is architecturally richer than 2D, because a volumetric city can support
levels a flat map cannot:

| Level | Shows | Analogous to |
|---|---|---|
| **Ecosystem** | Portals and connected partner-enterprise nodes (§12, §23 tier 5) | Looking at a map of cities |
| **Region / Holding** | One Enterprise per node/skyline-cluster (§11, §23 tier 2–4) | Looking at a city from an aircraft |
| **City** | All districts of one Enterprise, buildings as forms without floor-level detail | The 2D default view's 3D equivalent |
| **District** | One district's buildings at full detail, neighboring districts visible but de-emphasized | Standing at a district's edge |
| **Building** | One building's departments/floors (§10), inspector-level detail rendered spatially | Standing in front of, or inside, one building |

Descending a level is the same interaction at every tier (§11) — select → the camera moves one level
in → the next tier's detail resolves. Ascending reverses it. **A level is never skipped silently** — a
user always passes through the intermediate level's transition (§17) so spatial context is never lost,
even though the transition itself is brief.

---

## 15. Minimap

**Shipped (2D):** a compact dot-per-building overview (`.ec-minimap`) colored by visual state, in the
side rail — click a dot to pan-to that building without losing map context.

**Vision (3D):** the minimap becomes a **top-down radar** showing the current zoom level's contents
(buildings at District level, Enterprise nodes at Region level, etc.) plus a camera-frustum indicator
showing exactly what's currently in view — since a 3D camera can face any direction, the minimap is
what keeps a user oriented the way a fixed 2D viewport didn't need to. The minimap's coloring rules
(state-based dot color) carry over unchanged from 2D.

---

## 16. Navigation

The City's own in-page navigation surfaces (search, overlay toggles, context strip) are detailed in
§20. **For how the City fits into the platform's overall navigation system** (global search, Command
Palette, keyboard shortcuts, breadcrumbs) — see `ENTERPRISE_NAVIGATION.md`, which is the canonical
navigation-philosophy document; this file does not duplicate that content. The one fact worth
restating here: the City registers itself and every building into the platform's global search index,
so a query in the universal Command Palette anywhere in the product can resolve directly to a City
building, not only to the City's own local search box.

---

## 17. Interaction model

**Shipped (2D):**

| Action | Result |
|---|---|
| Click a building | Navigate to its real route — also sets focus, fires telemetry |
| Hover / keyboard-focus a building | Sets focus (inspector panel updates); does **not** navigate |
| Click a minimap dot | Pans the viewport to that building (`panTo`) — does not navigate |
| Type in City search | Filters buildings locally, shows top global-search hits; Enter opens top hit |
| Click an executive overlay toggle | Dims non-matching buildings — a filter, not a route change |
| Click zoom +/− / Reset | Adjusts or resets `viewport.zoom` |
| Click a header context-nav button | Navigates away, carrying a "decision" breadcrumb |
| Select an active workflow | Highlights that workflow's path, dims unrelated buildings |

**One consistent rule underlies all of this:** hover/focus is for *inspection*; click is for *action*.

**Vision (3D)** extends the same rule with pointer/spatial equivalents, never replacing it:

| Action (3D) | Result |
|---|---|
| Point/hover a building or Enterprise node | Sets focus, surfaces the same inspector panel content, positioned in 3D space near the focused object |
| Click/select | Same "descend one zoom level" behavior for a node (§14), or navigate to the real route if already at Building level |
| Drag / orbit | Rotates the camera around the current focus point — inspection only, never a navigation action by itself |
| Scroll / pinch | Moves one zoom level at a time (§14) — not a continuous zoom, unlike 2D |
| Double-click / double-tap a building | Skips the "descend" step and navigates directly to the real route — the 3D equivalent of 2D's single-click |
| Escape / Reset view | Returns to the last-used zoom level's default framing, not a fixed hardcoded camera position |

**The inspection/action distinction is the one interaction rule that must never differ between 2D and
3D** — a future 3D feature that makes hover navigate, or a drag gesture double as a route change, would
break the model users already rely on from 2D.

---

## 18. Camera behavior

**Shipped (2D):** the "camera" is a CSS transform on `.ec-plane` (`translate(x%, y%) scale(zoom)`) —
pan and zoom only, no rotation, no perspective. This is intentionally simple: 2D mode's whole design
goal is instant legibility, not cinematic framing.

**Vision (3D):** the camera is a real orbit/free camera with these designed behaviors:

1. **Always orbits around a focus point**, never free-flies without one — a camera with no subject is
   disorienting; the City always has one (the current building, Enterprise node, or district center).
2. **Framing is content-aware.** At District level the camera frames the whole district; at Building
   level it frames one building's face-on volume; the camera never requires a user to manually hunt for
   "a good angle" after a navigation action — arriving somewhere always arrives already well-framed.
3. **Transitions between focus points are camera moves, not cuts** (§13's "flight"), except where a
   user explicitly requests instant teleport.
4. **No idle camera drift.** Per the calm-motion rule (§2.5), the camera never slowly rotates or pans
   on its own while the user is inactive — an idle city is a still city, exactly like 2D's idle state.
5. **Reduced-motion respects camera behavior too.** A user with reduced-motion preference (`ENTERPRISE_
   DESIGN_SYSTEM.md` §5.5) gets instant camera cuts instead of flights, mirroring 2D's reduced-motion
   collapse of transition durations to near-zero — this is a hard requirement carried into 3D, not an
   optional nicety.

---

## 19. Animations & transitions

**Shipped (2D):** the City strictly follows Motion Design Language with its own "meaningful-only"
sub-rule:

| Animation | Trigger | Class |
|---|---|---|
| Soft page enter | Landing on `/enterprise-city` | `.edm-page-soft` |
| Focus breathe | A building is focused/hovered | `is-focused` → `edm-breathe` (2.4s) |
| State-change flash | A building's visual state changes | `edm-status-flash` (400ms) |
| AI pulse | Building has `aiActive` | `edm-pulse-soft` (1.6s infinite) — the one sanctioned continuous loop, only on the AI dot |
| Hover lift | Any building, on hover | `translateY(-2px)` + shadow transition |
| Viewport pan/zoom | Pan-to or zoom control | `.ec-plane` transform transition |

**Explicitly forbidden** (both modes): buildings "flying" into place on load, a constant ambient
zoom/pulse across the whole map, idle bounce, decorative traffic, confetti, or any looping animation
not tied to a genuine state change or AI activity.

**Vision (3D)** adds exactly two new transition types, both meaning-carrying, none decorative:

- **Growth transitions** (§22, §23) — when a new building/Enterprise node/district genuinely comes
  online (a new module enabled, a new subsidiary onboarded), it may animate a brief, one-time
  "construction/materialization" entrance the first time a user's city includes it — never repeating on
  subsequent visits, since a repeating "buildings appearing" animation would violate the no-decoration
  rule. This is the 3D city visually marking real organizational growth, once, truthfully.
- **Camera flight transitions** (§13, §18) — the between-building and between-zoom-level camera moves,
  timed within the same duration/easing budget as every other transition in the product
  (`ENTERPRISE_DESIGN_SYSTEM.md` §9), never a separate "cinematic" timing scale invented for the City.

---

## 20. In-City navigation surfaces

**Shipped (2D):** four complementary surfaces, all visible at once:

1. **Header context strip** — direct links to Dashboard, AI Concierge, Mission Control, Control Tower,
   Builder Studio, each phrased as a decision ("Decide on Dashboard," "Ask Advisor").
2. **Local search** — fuzzy-matches the City's own catalog and surfaces global search-index hits.
3. **Minimap** (§15) — pan-to-building without losing map context.
4. **Executive overlay toggles** (All / Health / Activity / AI) — lenses over the fixed map.

These carry over unchanged in 3D, with the minimap becoming the radar described in §15 and the header
strip's destinations unchanged regardless of rendering mode.

---

## 21. Workflows

The City is workflow-aware without owning workflow execution, in either mode:

- An existing workflow-automation source (reused, not reimplemented) produces an ordered list of
  building IDs a given workflow touches.
- **2D:** rendered as a bright dashed polyline through the buildings; non-path buildings dim.
- **3D (vision):** rendered as the transit path agent-markers travel along (§6, §13) — the workflow's
  building-to-building path becomes a literal, walkable/flyable route through the city, which is the
  City's most genuinely unique value versus any list-based workflow view, made even more concrete in 3D
  than in 2D.

---

## 22. How the city grows with module count

**Shipped principle, both modes.** The City's growth model is **catalog-driven and tenant-conditional**,
not spatially unbounded:

1. **New capability → new catalog entry, not a new engine.** Adding a building is adding one entry to
   the existing building catalog — a growing platform grows the catalog, not the architecture.
2. **Tenant-conditional rendering.** Building (and, at larger scale, Enterprise/Portal, §11–§12)
   visibility tracks the platform's existing per-tenant vertical enablement — never a City-specific
   enablement list.
3. **New districts before overcrowded districts.** Past roughly 6–8 buildings, open a new district
   with its own shape/massing language rather than cramming more into an existing one.
4. **Performance ceiling is explicit.** 2D is deliberately DOM/CSS (no WebGL) for low GPU cost; the
   guidance is to keep building count modest and virtualize off-screen buildings only if a tenant's
   module count pushes well past ~30–40 visible buildings — not to switch to WebGL/canvas as a first
   response. 3D's minimum viable renderer (WebGL or equivalent) is justified specifically by scale
   (§23) — it is not proposed as a 2D performance fix.
5. **Sub-buildings/departments over district explosion** for large verticals with many internal
   modules (§10) — the City's building count tracks *domains*, not every underlying repo module.
6. **The City never needs its own state model to grow.** Every growth path is satisfied by the existing
   building/status/identity data shapes; a growth idea that seems to need a new field type is a signal
   to check whether the underlying platform capability needs a new signal first (§2.1).

---

## 23. Scaling model: small company → holding → international enterprise → government → ecosystem

**Vision — the core new design of this document.** The City's structural concepts (Districts,
Buildings, Departments, Enterprises, Portals) exist specifically so the *same* product scales through
five tiers without a redesign at any step:

| Tier | What the City shows | Structural concept in use |
|---|---|---|
| **1. Small company** | One city: a handful of buildings across 2–3 districts (e.g. CRM, Finance, a Production building), no Hub-node view needed because there's only one Enterprise | Districts + Buildings (§8–§9) |
| **2. Holding** | One "city of cities": each subsidiary is one Enterprise node at Region zoom level (§14); descending into a node reveals that subsidiary's own full district/building layout | Enterprises (§11) |
| **3. International enterprise** | Same as Holding, plus geography as an organizing dimension — Enterprise nodes may cluster by region at the Region level (a City-of-cities view with a geographic, not just organizational, grouping), and cross-region workflow routes (§21) become genuinely long-distance visualizations of real cross-border business processes | Enterprises + Departments (regional sub-structure inside a large subsidiary's buildings) |
| **4. Government** | The same Holding/International structure, generalized: "subsidiaries" become "agencies/departments of government," each an Enterprise node; Security & Trust (§9.2) and Observability Deck (§9.2) buildings carry proportionally more weight (compliance/audit-heavy districts); public-facing services may be exposed through Portals (§12) to citizen-facing systems, with the same access-boundary rule as any other portal | Enterprises + Portals, with district emphasis shifted toward governance |
| **5. Ecosystem** | Multiple *separate organizations'* cities connected via Portals (§12) — a marketplace network, a supply chain, or a public/private partnership — no single mega-city merges everyone; each participant's city stays intact, with only the explicitly shared surfaces visible across each portal | Portals (§12), as the terminal structural concept |

**What stays constant across all five tiers (the actual design achievement):**
- The visual-state language (`ok/attention/critical/running/waiting/done`) means the same thing at
  every scale, from a single building to an Enterprise node representing an entire subsidiary.
- The "descend one level → see the next layer of detail" interaction (§14, §17) is identical at every
  tier — a user who has used the City at small-company scale already knows how to use it at government
  scale.
- The "every element is a real destination, no decoration" rule (§2.3, §13) never relaxes — an
  Ecosystem-scale Portal is exactly as governed and real as a single building's route.
- **No tier requires new backend architecture** — a government/ecosystem-scale City is a rendering
  question (how many levels, how the catalog is organized into Enterprises/Portals) over the same
  underlying platform capability model, never a new engine (§2.1, §22.6).

---

## Related documents

- `ENTERPRISE_DESIGN_SYSTEM.md` — the design canon the City inherits typography/color/motion/AI-voice
  rules from in both modes.
- `ENTERPRISE_NAVIGATION.md` — how the City fits into the platform's overall navigation system (§16).
- `AI_PRODUCTION_STUDIO.md` — a candidate future City building (§9.2) if that system ships.
- `docs/EP_05_ENTERPRISE_CITY.md`, `docs/ENTERPRISE_CITY_32_3_3.md` — historical sprint records for the
  shipped 2D foundation this document builds forward from.
- `ARCHITECTURE_MAP.md`, `MODULES.md` — the real module inventory §9.2's proposed buildings map onto.
- `CLAUDE.md` — "Enterprise City will be implemented only after all platform modules are completed":
  read alongside this document, that principle governs *when* the proposed/vision material here
  (§7.2, §9.2, §10–§12, §14's 3D levels, §23) should actually be built, not whether designing it now is
  premature.
