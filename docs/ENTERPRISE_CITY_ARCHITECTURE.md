# Enterprise City — Architecture v1

**Status:** permanent product architecture specification. Documentation only — no source code should be
modified as a result of reading this document. Authored as the platform's Chief Product Architect
function, extending — not replacing — `ENTERPRISE_CITY.md`.

## 0. Relationship to existing documents — and the one decision this document makes explicit

`ENTERPRISE_CITY.md` ("v0," 23 sections) remains the authoritative source for the **shipped 2D
implementation**: the real building catalog, exact CSS classes, exact coordinates, exact zoom range.
This document does not repeat that detail — it references it by section number throughout.

**The decision this document makes, and states plainly rather than burying:** `ENTERPRISE_CITY.md` §2
(philosophy point 6) and `00_MASTER_PRODUCT_BIBLE.md` currently describe the City as *"a companion to
the Dashboard, never a replacement... a user should be able to ignore the City entirely and lose no
capability."* This document is commissioned to design the City as **the primary navigation paradigm of
the platform** — a real elevation of the City's product role, not a restatement of the existing
position. Per `CLAUDE.md`'s "every architectural decision must be documented" and
`02_PRODUCT_PHILOSOPHY.md`'s own instruction to resolve ambiguity toward stated principles, this
document:

- **Documents the elevation explicitly**, here, rather than silently contradicting the prior framing.
- **Does not violate `CLAUDE.md`'s sequencing rule** — "Enterprise City is sequenced after platform-
  module completion" still governs *when* this architecture is built, not *whether* it's worth
  designing now (identical stance `ENTERPRISE_CITY.md` §7.2 and `10_ROADMAP.md` Horizon 3 already take
  for 3D mode). §23 of this document restates the migration/rollout implications directly.
- **Does not require Dashboard or Workspace to be removed or diminished.** "Primary navigation paradigm"
  means the City becomes the *default landing experience and the primary way capabilities are
  discovered and reached* — Dashboard remains the ~10-second briefing surface
  (`ENTERPRISE_DESIGN_SYSTEM.md` §14) and Workspace remains where sustained work happens
  (`ENTERPRISE_CITY.md` §5); both are now reached *through* the City rather than sitting beside it as
  co-equal home screens. This is a navigation hierarchy change, not a capability removal.
- **Recommends `ENTERPRISE_CITY.md` §2 point 6 and `00_MASTER_PRODUCT_BIBLE.md` be updated in a
  follow-up pass** to reflect this decision — flagged here, not silently done, since those files were
  not in this task's scope to edit.

## 1. City philosophy

The City is a **visual Enterprise Operating System**, not a game, not a decoration, and — as of this
document — not merely a companion view. Four literal equivalences anchor everything below:

| Metaphor | Means, concretely |
|---|---|
| Every building represents a business capability | One building = one real, navigable capability — never a decorative structure with no destination (`ENTERPRISE_CITY.md` §2.3, §9) |
| Every animation represents a system event | No animation plays without a real state change behind it (`ENTERPRISE_CITY.md` §2.5) — detailed fully in `ENTERPRISE_CITY_ANIMATIONS.md` |
| Every street represents navigation | Link lines and workflow routes are navigation/relationship structures, not literal roads (`ENTERPRISE_CITY.md` §13) |
| Every district represents a product domain | Districts are organizational groupings with a shared shape language, not arbitrary zones (`ENTERPRISE_CITY.md` §8) |

**The six-part quality bar** (this document's design-principles brief, translated into concrete
implications rather than left as name-dropped references):

| Reference | What it concretely contributes |
|---|---|
| Microsoft Flight Simulator control center | Instrument-panel clarity — real telemetry, readable at a glance, status-first; nothing is ambiguous about whether a system is healthy |
| Apple Human Interface | Restraint, deference, purposeful depth, accessibility as a first-class constraint, not an add-on |
| Google Maps | The pan/zoom/search mental model users already have; a minimap and a "you are here" anchor at every zoom level |
| Figma | Direct manipulation, live multiplayer presence, canvas performance that holds up at real scale |
| Notion | Calm typography, structured "blocks" (buildings behave like blocks), flexible hierarchy, keyboard-first power use |
| Unreal Engine | **Rendering-fidelity aspiration only** — real-time lighting/depth quality once 3D ships (§7 of `ENTERPRISE_CITY.md`, §22 below) — explicitly **not** game mechanics, spectacle, or "fun" framing; the City remains an Enterprise OS, never a game, even as its visual bar rises |

## 2. District system

Reuses `ENTERPRISE_CITY.md` §8 unchanged: five districts (Commerce, Ops, People, Intel, Hub), each with
a shape language expressed structurally, not just by color. As primary navigation paradigm, districts
gain one new responsibility: they are now the **first-level wayfinding structure** a new user learns —
onboarding (§8 below) teaches districts before it teaches individual buildings, since a returning user
should be able to say "Finance is in Commerce" long before they memorize a building's exact position.
New districts open per `ENTERPRISE_CITY.md` §22's rule (past ~6–8 buildings) — this document adds no
new district-creation mechanism.

## 3. Buildings

Reuses `ENTERPRISE_CITY.md` §9 (15 shipped, §9.2's proposed extension) unchanged. One new requirement
from the "primary navigation paradigm" elevation: **every capability reachable anywhere in the
platform must have a City building**, not just the currently-mapped Workspace/Platform-Builder surface.
This is a completeness bar, not a new mechanism — `ENTERPRISE_CITY.md` §9.2's proposed buildings (ERP
Center, Marketplace Plaza, Automation Yard, AI Studio, Security & Trust, Communications Tower,
Observability Deck) move from "nice to have" to "required before the City can honestly claim primary
status" — see §23's rollout gate.

## 4. Building states

Summarized here; the complete state model (transitions, precedence rules, source-of-truth mapping) is
`ENTERPRISE_CITY_STATES.md`. The six requested states map onto the existing shipped visual-state
language (`ENTERPRISE_CITY.md` §9, `CityVisualState`) plus one genuinely new state:

| Requested state | Maps to | Status |
|---|---|---|
| Active | `running`/`ok` | Real, shipped |
| Warning | `attention` | Real, shipped |
| Offline | *(new — no direct equivalent today)* | Designed — see `ENTERPRISE_CITY_STATES.md` §3 |
| Busy | `running` (tone `busy`) | Real, shipped |
| AI working | the `aiActive`/AI-dot signal, orthogonal to the six visual states | Real, shipped |
| User present | *(new — collaboration presence)* | Designed, builds on `WORKSPACE_INTERACTIONS.md` §21 |

## 5. Enterprise map

The map is the City's top-level canvas — one Enterprise's full district/building layout at the "City"
zoom level (§7), or, for multi-entity tenants, a "city of cities" at the "Region" level via the
Enterprises concept (`ENTERPRISE_CITY.md` §11). As primary navigation paradigm, the Enterprise map is
what a user sees **immediately after login** (§8) rather than optionally navigating to — this is the
single largest concrete product change this document makes versus v0's positioning.

## 6. Camera behavior

Reuses `ENTERPRISE_CITY.md` §18 unchanged for both modes: 2D's CSS transform (pan/zoom, no rotation) and
3D's orbit-around-focus camera (vision). One addition specific to "primary navigation paradigm": the
camera's **default framing on login** must resolve instantly (no loading spinner as primary chrome,
consistent with `ENTERPRISE_DESIGN_SYSTEM.md` §5.4's forbidden list) — a primary landing surface cannot
have a worse perceived load time than the Dashboard it's replacing as the default view.

## 7. Zoom levels

Reuses `ENTERPRISE_CITY.md` §14 unchanged: 2D's continuous 0.75–1.4 scale (informal Overview/Default/
Focus bands) today; 3D's discrete Ecosystem → Region → City → District → Building levels as vision. As
primary navigation paradigm, the **City level (2D's "Default" band) is the new home position** — where
"home" used to mean the Dashboard route, it now means this zoom level/framing of the Enterprise map.

## 8. Navigation model

The City becomes the top of `ENTERPRISE_NAVIGATION.md`'s navigation hierarchy, without changing that
document's underlying mechanics:

- **Login → City (Enterprise map, City zoom level), not Dashboard.** Dashboard becomes one reachable
  destination among the City's Hub-district buildings (already true structurally — "Command Center
  (Dashboard)" is a real shipped building, `ENTERPRISE_CITY.md` §9.1) — it becomes the destination the
  City's Hub building leads to, not a separate top-level route competing with the City for "home."
- **The Command Palette (`ENTERPRISE_NAVIGATION.md` §8) remains reachable from every City zoom level**
  — the City is the spatial paradigm, the Palette is the fast-path paradigm; they are complementary,
  not competing, exactly as `ENTERPRISE_NAVIGATION.md` §1 already establishes for every other surface.
- **The Dock (`ENTERPRISE_NAVIGATION.md` §9) persists over the City exactly as it does over every other
  surface** — no City-specific chrome exception.
- **Breadcrumbs resolve from the City's own position** — descending from Ecosystem → Region → City →
  District → Building (§7) produces a breadcrumb trail via the existing `breadcrumbEngine`
  (`ENTERPRISE_NAVIGATION.md` §11), extended with City-specific `level` values rather than a second
  breadcrumb system.
- **New-user onboarding teaches the City first.** Since the City is now the primary paradigm, first-run
  onboarding should orient a new user at the District level (§2) before ever showing individual
  buildings — this mirrors how a real city's visitor learns neighborhoods before street addresses.

## 9. Keyboard navigation

Extends `ENTERPRISE_NAVIGATION.md` §16's global shortcut table with City-specific bindings, all
resolvable through the same `Escape`/`Ctrl+Tab` conventions already established:

| Shortcut | Action |
|---|---|
| `Arrow keys` | Move focus between adjacent buildings (District-aware — arrows move within a district before crossing into a neighboring one) |
| `Enter` | Navigate to the focused building's real route (the keyboard equivalent of click, per `ENTERPRISE_CITY.md` §17's inspection/action rule) |
| `Tab` / `Shift+Tab` | Cycle focus across all buildings in catalog order, independent of spatial position — the accessibility fallback for a user who can't reliably use directional arrows |
| `+` / `-` | Zoom in/out (2D continuous; 3D discrete level change, §7) |
| `Ctrl/Cmd+Shift+City-shortcut` *(reserved, exact binding TBD at implementation)* | Jump straight to the City from anywhere, mirroring `Ctrl+Tab`'s Quick Switcher pattern |
| `Escape` | Clear focus / return to the last-used framing — consistent with every other surface's Escape behavior (`ENTERPRISE_NAVIGATION.md` §16) |

This table is the canonical addition to `ENTERPRISE_NAVIGATION.md` §16 once implemented — it should not
fork into a second, City-only shortcut reference.

## 10. Mouse interaction

Reuses `ENTERPRISE_CITY.md` §17 unchanged (hover/focus = inspect, click = act, drag minimap = pan) and
`WORKSPACE_INTERACTIONS.md`'s general rules where applicable. As primary navigation paradigm, one
addition: **right-click on a building surfaces a context menu** (using the shared `ContextMenu`
primitive `WORKSPACE_INTERACTIONS.md` §5 designs) with quick actions — "Open," "Pin to favorites,"
"Open in new tab" (once tabs exist for City destinations, `WORKSPACE_INTERACTIONS.md` §9) — rather than
requiring a full navigate-then-return round trip for common secondary actions.

## 11. Touch interaction

Reuses `ENTERPRISE_NAVIGATION.md` §17's touch principles directly: pinch-to-zoom (mapping to the same
zoom mechanism as +/- buttons, §7), tap = focus/inspect, double-tap = navigate (the touch equivalent of
click, consistent with `ENTERPRISE_CITY.md` §17's 3D-vision interaction table), long-press = context
menu (§10's context menu, touch-equivalent per `ENTERPRISE_NAVIGATION.md` §17). Swipe pans the viewport.
See §22 for whether the City is the primary paradigm on mobile specifically — the answer is nuanced, not
a flat yes.

## 12. Animation language

Summarized here; full detail (every animation with its triggering event, exact timing token, and the
forbidden list) is `ENTERPRISE_CITY_ANIMATIONS.md`. The one rule worth stating at the architecture
level: **"every animation represents a system event" is not a slogan, it is a validation rule** — a
proposed City animation that cannot name the specific state change it represents should be rejected in
review, the same way a hardcoded color value is rejected under `ENTERPRISE_DESIGN_SYSTEM.md` §7's token
rule.

## 13. Runtime visualization

**New scope, not present in `ENTERPRISE_CITY.md` v0.** As primary navigation paradigm, the City should
visualize the platform's actual runtime health, not only per-building business-status:

- **System-wide runtime signals** (API health, job-queue depth from `platform_jobs`, event-bus activity
  from `PlatformEventBus`, `ARCHITECTURE_MAP.md` §2) surface as an ambient, city-wide indicator — e.g. a
  subtle overall-sky/atmosphere tint (tied to §17's Day/Night mechanism, reusing its token infrastructure
  rather than inventing a second one) reflecting aggregate platform health, distinct from any single
  building's status.
- **Never a second status language.** Runtime visualization reuses the exact same
  `ok/attention/critical/running/waiting/done` vocabulary (`ENTERPRISE_CITY.md` §9) at the whole-city
  level that a building uses at its own level — consistent with `ENTERPRISE_CITY.md` §11's rule that an
  Enterprise node glows under "the same rules a building tile does."
- **Sourced from real telemetry only** (`platform_observability`, `MODULES.md` §3) — this visualization
  must not be invented from synthetic/demo data once built; if the real signal isn't wired yet, the
  ambient indicator should be omitted rather than faked, per `02_PRODUCT_PHILOSOPHY.md` principle 9.

## 14. AI Agent visualization

Reuses `ENTERPRISE_CITY.md` §6 unchanged: the AI dot as a per-building signal (2D, real), and agent
transit markers traveling along workflow routes (3D, vision) as the one sanctioned "traveling object"
exception to the no-decorative-motion rule. As primary navigation paradigm, the AI overlay filter
(`ENTERPRISE_CITY.md` §20) becomes one of the most-used lenses, not an occasional executive tool — worth
flagging for implementation priority (§24) rather than a new design requirement.

## 15. Notification visualization

Real today (`ENTERPRISE_CITY.md`'s `CityLiveStatus.notifications` badge count, cross-referenced with
`ENTERPRISE_NAVIGATION.md` §12's real notification store) — a building's badge count is already sourced
from the same notifications a user sees in the Notifications Panel. As primary navigation paradigm, this
becomes the **first place a user sees "something needs attention"** rather than the Dashboard's card
list or the Dock's bell badge alone — all three must stay synchronized to one source, never three
independently-drifting counts (a direct instance of `02_PRODUCT_PHILOSOPHY.md` principle 7).

## 16. Collaboration visualization

Builds directly on `WORKSPACE_INTERACTIONS.md` §21–§22 (live presence, cursor sharing), which already
names Enterprise City as the primary use case for spatial cursor-sharing ("scoped to spatial/canvas
surfaces only... Enterprise City"). As primary navigation paradigm:

- **Presence indicators** (avatar stack, §21 there) show which colleagues are currently in the City and,
  where known, which district/building they're focused on.
- **Cursor sharing** is the concrete mechanism — a colleague's named, color-coded cursor visible on the
  map, ambient and non-blocking (§22 there), never creating an exclusive lock on a building another user
  is also viewing.
- **Still vision, not shipped** — §0's grounding discipline applies here as much as anywhere: this
  section designs the target, `WORKSPACE_INTERACTIONS.md` §0 already confirms zero existing precedent.

## 17. Day/Night mode

**New, designed to reuse the existing theme engine, not invent a fifth theme**
(`ENTERPRISE_DESIGN_SYSTEM.md` §4: `light | dark | corporate | custom`). Day/Night is a **City-specific
presentational reading** of the existing light/dark tokens, not a new token set:

- **Day** maps to the light theme's token values; **Night** maps to the dark theme's — the City does
  not define its own color pairs.
- **Two trigger models, both designed:** (a) tied to the tenant's real business hours/timezone
  (meaningful — "it's after-hours for this business" is a real fact worth reflecting, consistent with
  §12's "represents a system event" rule generalized to *time* as a signal), or (b) a manual user toggle
  independent of system theme (the same relationship the OS-level theme cycling button already has,
  `ENTERPRISE_NAVIGATION.md` §10). **Recommendation: default to (a), always allow manual override** —
  automatic-but-overridable is the pattern this platform already uses for reduced-motion and contrast
  preferences (`ENTERPRISE_DESIGN_SYSTEM.md` §5.5, §4).
- **The transition between Day and Night is itself an animation representing a real event** (time
  crossing a threshold) — detailed in `ENTERPRISE_CITY_ANIMATIONS.md`, not a decorative sunset effect.

## 18. Weather effects (optional)

Explicitly marked optional by this task, and this document's recommendation is **conditional, not a
flat yes** — because unconstrained weather effects directly risk `ENTERPRISE_DESIGN_SYSTEM.md` §5.4's
forbidden list (no decoration, no ambient loops) and `02_PRODUCT_PHILOSOPHY.md` principle 3 (calm, not
decorative). Two designs were considered:

- **Rejected: cosmetic/randomized weather** (rain, clouds cycling for visual variety). This would be
  the single clearest violation of "every animation represents a system event" (§1) anywhere in this
  document — explicitly **not recommended**.
- **Recommended, if built at all: data-bound "weather" as a system-health metaphor.** Overcast/storm
  visuals map to real, aggregate negative signal (e.g., multiple districts in `attention`/`critical`
  state simultaneously) — the same underlying idea as §13's runtime-visualization sky tint, described
  with weather vocabulary instead of a status tint. Framed this way, "weather" is not a new concept, it
  is a more evocative skin on §13 — which means **it should not be built as a separate feature**, only
  as an alternate visual treatment of the same runtime-health signal, subject to the same
  real-telemetry-only rule (§13).
- **If in doubt, omit it.** Weather is the one item in this entire specification where "don't build it"
  is a legitimate, principle-consistent answer — see §24's implementation priority.

## 19. Enterprise branding

Reuses `ENTERPRISE_DESIGN_SYSTEM.md` §4's `custom` theme + `BrandOverrides` (primary color, primary-
soft, font) and `AI_PRODUCTION_STUDIO.md` §14's Brand Library field shape — the City's building color
accents and Hub-district emphasis re-tint from the tenant's brand primary color exactly as every other
surface does. **District shape language (§2) never changes per brand** — a tenant's Commerce district
buildings stay softly-rounded regardless of brand, only color/accent shifts. This is the same
"structure is fixed, tokens are swappable" rule `ENTERPRISE_DESIGN_SYSTEM.md` already applies platform-
wide, restated for the City specifically so a future implementer doesn't invent a City-specific
branding override mechanism.

## 20. Accessibility

The hardest open design problem in this document, stated honestly rather than glossed over: **a
spatial map is inherently a visual paradigm**, and this platform's principle that "text always works"
(`02_PRODUCT_PHILOSOPHY.md` principle 8) cannot be satisfied by making the map itself accessible alone.
The design requirement:

- **A first-class, non-spatial "List View" of the City must exist alongside the map**, not as a
  degraded fallback — the same building catalog, the same live status, the same search, rendered as a
  structured list/table (reusing `DataGrid`/`Table` primitives, `ENTERPRISE_DESIGN_SYSTEM.md` §13's
  catalog) with full keyboard and screen-reader support. A screen-reader user's primary path through
  "the primary navigation paradigm" is this list, not a described version of the map.
- **Every interaction in §9–§11 has a keyboard equivalent already designed** — Tab-cycling (§9) is
  specifically included as the accessibility-first alternative to spatial arrow-navigation, not an
  afterthought bolted onto a mouse-first design.
- **Reduced motion is inherited unmodified** (`ENTERPRISE_DESIGN_SYSTEM.md` §5.5, `ENTERPRISE_CITY.md`
  §19) — every City-specific animation in `ENTERPRISE_CITY_ANIMATIONS.md` has a defined reduced-motion
  behavior before it ships, not after.
- **Color is never the only signal** — every state (`ENTERPRISE_CITY_STATES.md`) pairs its color with a
  distinct silhouette/shape and a text label, consistent with `ENTERPRISE_DESIGN_SYSTEM.md`'s existing
  "never rely on color alone" component-catalog rule for charts.

## 21. Performance strategy

Reuses `ENTERPRISE_CITY.md` §22's existing guidance (DOM/CSS map, virtualize past ~30–40 visible
buildings) with higher stakes attached, since a primary navigation paradigm is used on every session,
not occasionally:

- **Instant first paint is now a hard requirement** (§6) — the City cannot have a worse perceived load
  time than the Dashboard route it is replacing as the default landing view.
- **Live-status polling must not block interaction.** Building tiles render immediately from cached/
  last-known state; live updates apply incrementally (consistent with the existing 12-second poll
  cadence, `ENTERPRISE_CITY.md` §22) — a user should never wait on a network round-trip to see *a*
  city, only to see it *fresh*.
- **Virtualization threshold is now a launch-blocking requirement, not future work**, given §3's
  completeness bar (every capability gets a building) will push building counts toward the 30–40 range
  faster than v0's more limited scope did.
- **3D (once built, §22) inherits its own render-budget discipline** from standard real-time rendering
  practice — out of scope for this documentation-only pass beyond naming it as a requirement for §23's
  migration.

## 22. Mobile adaptation

Reuses `ENTERPRISE_DESIGN_SYSTEM.md` §18's responsive rules and `ENTERPRISE_NAVIGATION.md` §17's touch
principles, with one honest exception this document states plainly rather than forcing a bad fit:
**the City is not necessarily the primary paradigm on mobile.** A spatial map's value is highest on a
large viewport with room to see multiple districts at once; on a phone-sized viewport, a structured list
(§20's accessible List View, repurposed as the *default* mobile view, not only the accessibility
fallback) may serve users better than a cramped, heavily-panned map. **Recommendation:** mobile defaults
to List View with the map available as an explicit "Map View" toggle, while desktop/tablet default to
the map — this is a considered exception to "one primary paradigm everywhere," not an oversight, and it
should be documented as such rather than silently diverging.

## 23. Future 3D migration strategy

Reuses `ENTERPRISE_CITY.md` §7.2 and `10_ROADMAP.md` Horizon 3 unchanged: one data model, two
renderings; 3D is a richer lens, never a richer product; mode switching preserves focus/viewport state
across the switch. This document's addition, specific to the "primary navigation paradigm" elevation:

- **2D remains the default for most tenants indefinitely.** 3D is scoped, per `ENTERPRISE_CITY.md` §23,
  to organizations large enough that a flat map's legibility strains (Holding tier and above) — 3D
  migration is not a universal upgrade path every tenant eventually takes, it is a scale-appropriate
  option.
- **The elevation to "primary paradigm" applies to 2D City first.** 3D's migration timeline is
  unaffected by this document's navigation-hierarchy decision — it remains gated by `CLAUDE.md`'s
  platform-module-completion rule exactly as `10_ROADMAP.md` Horizon 3 already states, independent of
  whether 2D City is the default landing view.

## 24. Summary, risks, priority, and sprint sequence

### Architecture summary

This document elevates Enterprise City from a companion, optional view to the platform's primary
navigation paradigm — logging in lands a user in the City (District/City zoom level) rather than the
Dashboard, with Dashboard and Workspace now reached *through* it. The elevation is achieved without a
new engine (§0's constraint, inherited from `ENTERPRISE_CITY.md` §2.1): it reuses the existing building
catalog, visual-state language, motion system, and theme engine throughout, adding exactly four
genuinely new subsystems — Runtime Visualization (§13), Collaboration Visualization (§16), Day/Night
mode (§17), and (conditionally) Weather-as-health-metaphor (§18) — and one new completeness requirement
(§3: every platform capability must have a City building before the elevation is honest).

### UX risks

1. **Accessibility risk (highest).** A primarily-spatial navigation paradigm is a real regression for
   screen-reader and keyboard-only users unless the List View (§20) ships as a true first-class parallel
   experience, not a lesser fallback built after the map. This is this document's single largest risk.
2. **Onboarding risk.** New users who don't yet know the district vocabulary (§2) may find "log in to a
   map" more disorienting than "log in to a dashboard" — mitigated by §8's district-first onboarding
   design, but unverified without real user testing.
3. **Performance risk at completeness scale.** §3's "every capability gets a building" requirement,
   combined with the platform's real ~106-package module count (`MODULES.md`), pushes building counts
   well past the virtualization threshold (§21) faster than v0 anticipated — this is a real engineering
   risk, not just a design one.
4. **Mobile fragmentation risk.** §22's considered exception (List View default on mobile) means the
   platform genuinely has two "primary" paradigms depending on device — a coherence risk that must be
   documented clearly to every future contributor, or it will read as an inconsistency rather than a
   deliberate choice.
5. **Scope-creep risk from Weather/Day-Night.** Both are exactly the kind of feature that drifts from
   "meaningful signal" toward "looks cool" over successive sprints — §17–§18's constraints need active
   enforcement in review, not just documentation.

### Implementation priority

1. Building-catalog completeness (§3) — the prerequisite for the elevation being honest at all.
2. Accessible List View (§20) — must ship alongside, never after, any change to make the map the
   default view.
3. Login-lands-in-City navigation change (§8) — the core product change.
4. Performance/virtualization work (§21) — required before #1's completeness expansion ships broadly.
5. Keyboard navigation table (§9) and mobile List-View-default (§22).
6. Notification/runtime visualization (§13, §15) — real-telemetry-gated, ship only once the underlying
   signals exist.
7. Collaboration visualization (§16) — depends on presence/cursor infrastructure that doesn't exist yet
   anywhere in the platform (`WORKSPACE_INTERACTIONS.md` §0).
8. Day/Night (§17) — low risk, low urgency, can land any time after #1–#5.
9. Weather-as-health-metaphor (§18) — lowest priority; acceptable to omit indefinitely.
10. 3D migration (§23) — governed entirely by `10_ROADMAP.md` Horizon 3's existing gate, not this
    document's timeline.

### Recommended Cursor sprint sequence

| Sprint | Focus |
|---|---|
| **City Architecture 1.1** | Building-catalog completeness audit — enumerate every real platform capability missing a City building (§3), against `MODULES.md`; no map/navigation change yet |
| **City Architecture 1.2** | Accessible List View as a true parallel surface (§20) — ships as an equal, not a fallback |
| **City Architecture 1.3** | Login-lands-in-City navigation change (§8), keyboard navigation table (§9), mobile List-View-default (§22) |
| **City Architecture 1.4** | Virtualization and performance hardening (§21) at the completed building count from 1.1 |
| **City Architecture 1.5** | Runtime visualization (§13) and notification-source unification (§15), gated on real telemetry availability |
| **City Architecture 1.6** | Day/Night mode (§17) |
| **City Architecture 2.0** | Collaboration visualization (§16) — sequenced as its own major version, since it depends on presence/cursor infrastructure with zero existing precedent anywhere in the platform |
| *(Weather, §18)* | Not scheduled — revisit only if a concrete, data-bound design need arises; do not schedule speculatively |
| *(3D migration, §23)* | Governed by `10_ROADMAP.md` Horizon 3's existing platform-module-completion gate, not this sequence |

## Related documents

- `ENTERPRISE_CITY.md` — the authoritative shipped-implementation reference this document extends.
- `ENTERPRISE_CITY_STATES.md`, `ENTERPRISE_CITY_ANIMATIONS.md`, `ENTERPRISE_CITY_UI_RULES.md` — the
  three companion specifications this document summarizes and delegates full detail to.
- `ENTERPRISE_NAVIGATION.md` — the platform-wide navigation model the City now sits atop.
- `WORKSPACE_INTERACTIONS.md` — the interaction/collaboration substrate §16 builds on.
- `ENTERPRISE_DESIGN_SYSTEM.md` — the token/motion/theme canon every section here inherits.
- `10_ROADMAP.md`, `TECH_DEBT.md` — sequencing and debt tracking for this document's implementation
  priority (§24).
- `00_MASTER_PRODUCT_BIBLE.md` — recommended for a follow-up update reflecting §0's decision.
