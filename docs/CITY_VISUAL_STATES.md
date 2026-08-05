# Enterprise City — Visual States & Living-World Elements

**Sprint:** CG-9 — Architecture Research + UI Research + Game Design Research. Documentation only, no
source code was modified.

**Do not duplicate:** `CITY_ANIMATION_SYSTEM.md` (CG-2) and `ENTERPRISE_CITY_ANIMATIONS.md` already
own the platform's animation *governance* — durations, easing, the reduced-motion contract, the
sanctioned-continuous-loop allowlist, and the one governing rule: **"every animation represents a
system event."** This document does not re-litigate that rule — it applies it, strictly, to ten new
visual concepts the brief asks for, several of which (drones, robots, weather) are exactly the kind of
element that could violate it if built carelessly. Every element below is specified with the real
signal it represents; an element this document could not tie to a real signal is marked **not
recommended**, not quietly included anyway.

## 0. The one test every element in this document must pass

Restated from `ENTERPRISE_CITY_ANIMATIONS.md` §0, applied here as a literal checklist: **can this
document name the specific real event this visual represents?** If the honest answer is "it would just
look nice," the element does not belong in Enterprise City, however common it is in city-building game
genre conventions. This document is explicitly grounded in **Game Design Research** as one of its
modes — the research finding worth stating plainly is that most "living city" game conventions
(ambient pedestrians, decorative weather cycles, background traffic) are built to *simulate* liveliness
where none exists. Enterprise City's liveliness is real (buildings genuinely reflect live state) — so
every element below is designed to represent that real liveliness more richly, never to fake liveliness
that isn't there.

## 1. Road traffic — REAL mechanism exists, extend carefully

**Real today** (CG-3): `.ec-link-line.is-flowing` — confined to links touching the focused building,
gated by effects layer/quality/reduced-motion. **SPEC extension**: widen the real flow trigger from
"touches the focused building" to "touches an in-flight workflow's `cityPath`" (`CITY_SIMULATION.md`
§5's Running-workflows row) — still confined to specific links, never ambient background traffic on
idle roads. **Not recommended**: continuous low-level "ambient traffic" on every road regardless of
activity — this is precisely the fake-liveliness pattern §0 warns against.

## 2. Pedestrians — not recommended as literal figures; SPEC as an abstraction of presence

A literal walking-pedestrian sprite has no real signal to represent — City has no per-user avatar
model today (`CITY_COLLABORATION.md` §0, CG-5: presence is entirely SPEC, no real backing). **SPEC**:
if `CITY_COLLABORATION.md`'s presence work ever ships, "pedestrians" should be the same real
`focusBuildingId`-driven presence dot that document already specifies (§3, co-presence), never a new,
separately-simulated crowd of decorative figures. **Not recommended**: any pedestrian that isn't a real
user's real presence.

## 3. Flying drones — SPEC, the clearest real analog already exists

`CITY_SIMULATION.md` §2.2 (CG-4) already specifies "Agent movement" — an agent icon traveling between
buildings, reusing `cameraEngine`'s target-resolution pattern, confined to the one sanctioned
traveling-object rule (`ENTERPRISE_CITY_ANIMATIONS.md` §3). **A "drone" is simply this document's game-
design vocabulary for that same real spec** — a small aerial marker rather than a ground-level one,
representing the identical real signal (an AI agent or job handing off between buildings). This
document does not propose a second traveling-object primitive under a different name; "drone" is a
skin on the agent-movement marker, not a new mechanism.

## 4. Delivery robots — SPEC, same mechanism as drones, different real trigger

Where a "drone" (§3) represents an *agent* handoff, a "delivery robot" is proposed as the same marker
representing a *job/task* handoff specifically (`CITY_SIMULATION.md` §2.4's "Workflow execution" row —
the building-grain version of agent movement). Two visual skins, one real mechanism, two distinct real
triggers — not two new systems. **Not recommended**: robots that appear for cosmetic variety rather
than a specific job handoff.

## 5. Building lighting — REAL foundation exists via the theme engine, SPEC for activity-driven lighting

**Real today**: `graphicsTheme.ts` (CG-2) already themes the whole City (Light/Dark/Enterprise/Cyber),
and every building's real state classes (`ec-state-*`) already drive background/border color via
`color-mix()` tokens. **SPEC**: a building's *window lighting density* (how many small "lit window"
accents render) scales with its real `tasks`/`aiActive` fields — a busy building looks lit-up, an idle
one looks dark — reusing the exact same `CityLiveStatus` fields the state-color system already reads,
not a new data source. This is the single highest-value "game design" idea in this document precisely
because it's a pure CSS/data-reuse trick, zero new state.

## 6. Smoke — not recommended

No real signal a "smoke" visual would represent was identified. The closest tempting real analog
(a building in `Critical`/`Error` state) is already correctly represented by the real state-color
system (red-family border/background) and the real `edm-status-flash` animation — adding smoke on top
would be redundant decoration for a signal already visually communicated, exactly the pattern §0
warns against. **Not recommended.**

## 7. Energy — SPEC, as a citywide aggregate, not a per-building effect

Proposed as a rename/reframe of `CITY_SIMULATION.md` §2.6's real "Background processing" aggregate
badge (CG-4, `aiAgentRuntime.activeCount()`) — "the city's energy level" is a game-design-friendly name
for the same real citywide AI-activity aggregate already specified. No new per-building "energy" glow
is proposed — that would duplicate the real `pulse`/lighting (§5) mechanisms already covering that
signal at building grain.

## 8. Billboards — SPEC, small and real-data-bound

Proposed: a small rotating callout on Plaza or a district label surfacing one real, current
`cityAdvice`/`advisorHintForBuilding` recommendation (both real, `cityVisualLanguage.ts`/
`enterprise-workflow`) — i.e., a "billboard" is a spatial presentation of the real Advisor content
already shown in the sidebar today, not a new content source. **Not recommended**: any billboard
content not sourced from a real, existing recommendation/notification feed — a billboard that
displays static marketing-style copy would be decoration, not information.

## 9. Weather effects — not recommended as literal weather; SPEC as the real health-ambient signal already proposed

`ENTERPRISE_CITY_ANIMATIONS.md` §3 (cited in `CITY_RUNTIME.md`'s research) already proposes a
"Runtime/health ambient shift" — a slow citywide tint cross-fade tied to aggregate platform health —
and explicitly rejects literal cosmetic weather as an alternate skin of that same signal *unless* it
shares the exact same trigger/timing, never as an independent decorative system. This document
restates that rejection rather than re-opening it: **if weather is ever built, it is a re-skin of the
real health-ambient signal, sharing its trigger exactly** — never randomized, never decorative,
never on its own clock.

## 10. District highlighting — REAL mechanism exists

**Real today** (CG-3): `district_activation` (`.ec-district-label.is-activated`, reuses the real
`edm-status-flash` keyframe) fires on `jumpDistrict()`. **SPEC extension**: also fire on a district
crossing into `dominantState: "critical"` (`CITY_SIMULATION.md` §1.2's proposed `DistrictRuntimeSummary`
aggregate, CG-4) — so a district can highlight itself to draw attention, not only in response to a
user's own navigation click. This is the one element in this document that's almost entirely already
specified elsewhere; restated here for completeness of the requested list.

## 11. Summary table

| Element | Status | Real mechanism reused |
|---|---|---|
| Road traffic | Real, SPEC extension | `.ec-link-line.is-flowing` (CG-3) |
| Pedestrians | SPEC (presence-gated) | `CITY_COLLABORATION.md` presence dot (CG-5) |
| Flying drones | SPEC (skin, not new mechanism) | Agent-movement marker (`CITY_SIMULATION.md` §2.2, CG-4) |
| Delivery robots | SPEC (skin, not new mechanism) | Job-handoff marker (`CITY_SIMULATION.md` §2.4, CG-4) |
| Building lighting | Real foundation + SPEC extension | `CityLiveStatus` fields + `graphicsTheme.ts` (CG-2) |
| Smoke | **Not recommended** | Redundant with real state-color system |
| Energy | SPEC (rename of existing spec) | Background-processing aggregate (`CITY_SIMULATION.md` §2.6, CG-4) |
| Billboards | SPEC (real-data-bound only) | `cityAdvice`/`advisorHintForBuilding` (real) |
| Weather effects | **Not recommended** as literal weather | Health-ambient re-skin only (`ENTERPRISE_CITY_ANIMATIONS.md`) |
| District highlighting | Real, SPEC extension | `district_activation` (CG-3) |

## 12. Non-goals

- No decorative element is proposed anywhere in this document without a named real signal — two
  elements (Smoke, literal Weather) are explicitly rejected on exactly this basis.
- No second traveling-object mechanism — drones and delivery robots are both skins on the one real
  agent/job-movement marker.
- No new per-building visual data source — every element reuses `CityLiveStatus`, `cityAdvice`, or an
  already-specified CG-4 aggregate.

## Related documents

`CITY_ANIMATION_SYSTEM.md`/`ENTERPRISE_CITY_ANIMATIONS.md` (the governing motion rule this whole
document applies), `CITY_SIMULATION.md` (agent/job movement, background processing, district
aggregation — the real mechanisms §3/§4/§7/§10 reuse), `CITY_COLLABORATION.md` (presence, §2's
dependency), `CITY_BUILDING_STATES.md` (the state-color system §5/§6 build on).
