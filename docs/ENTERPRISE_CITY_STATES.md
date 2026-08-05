# Enterprise City — Building States Specification

**Status:** permanent specification. Companion to `ENTERPRISE_CITY_ARCHITECTURE.md` §4. Documentation
only — no source code should be modified as a result of reading this. This is the complete state model
for every building (and, by the same rules, every Enterprise node and district rollup,
`ENTERPRISE_CITY.md` §11) in the City.

## 0. Grounding — what's real today

`ENTERPRISE_CITY.md` §9 and `cityVisualLanguage.ts` (real, shipped) define six visual states —
`ok, attention, critical, running, waiting, done` — resolved from a `CityLiveStatus` record (`tone`,
`notifications`, `tasks`, `aiActive`, `processLabel`) by `resolveVisualState()`. This document maps the
architecture's six requested states onto that real system, adds the two genuinely new states
(**Offline**, **User present**) as designed extensions, and defines precedence rules that don't exist
yet in the shipped code (today's real resolver has an implicit precedence order; this document makes it
explicit and extends it).

## 1. The state set

| State | Real today? | Shipped equivalent | Meaning |
|---|---|---|---|
| **Active** | Yes | `running` (tone `active`) / `ok` | The capability is operating normally, with visible current activity |
| **Warning** | Yes | `attention` | The capability needs human attention — elevated notification/task count, or a flagged health check |
| **Offline** | **New** | — | The capability is unreachable or intentionally disabled for this tenant (§3) |
| **Busy** | Yes | `running` (tone `busy`) | The capability is under heavy load or processing a large queue right now |
| **AI working** | Yes, orthogonal | `aiActive` flag + AI dot | An AI agent is actively operating within this capability right now — layered on top of any of the above, not a replacement for them |
| **User present** | **New** | — | One or more colleagues are currently viewing or focused on this building (§4) |

**Two of these six are orthogonal overlays, not points on the same scale:** *AI working* and *User
present* can co-occur with *Active*, *Warning*, or *Busy* simultaneously (a building can be `Busy` **and**
have AI working in it **and** have a colleague present, all at once) — only *Offline* is mutually
exclusive with every other state (§5).

## 2. State sourcing — what real signal drives each state

| State | Source | Notes |
|---|---:|---|
| Active | `CityLiveStatus.tone === "active"` or `"ok"`, low notification/task count | Default resting state |
| Warning | `notifications >= 3 \|\| tasks >= 5`, or a linked health-check failure (`ENTERPRISE_CITY.md`'s `useCityLiveStatus` health-check cross-reference) | Threshold-based, already real |
| Busy | `tone === "busy"` | Set directly by domain logic (e.g. AI Team/Concierge alternate busy/active on a poll cadence) |
| AI working | `CityLiveStatus.aiActive` | Independent boolean, not derived from tone |
| Offline (new) | The building's underlying route/service reports unreachable (health-check failure with no data), **or** the tenant has not enabled the corresponding vertical/module (`platform_management` vertical enablement, `ARCHITECTURE_MAP.md`) | Two distinct causes, same visual state — see §3 for why they must still read identically |
| User present (new) | A live presence signal (`WORKSPACE_INTERACTIONS.md` §21, vision) reporting one or more active viewers scoped to this building | Requires the presence infrastructure `WORKSPACE_INTERACTIONS.md` §0 confirms does not exist yet |

**Rule:** no state may be set from synthetic/demo data once built — an unwired signal should leave a
building in its last-known real state (or `Active`/default) rather than fabricate one, per
`02_PRODUCT_PHILOSOPHY.md` principle 9 applied to state resolution specifically.

## 3. Offline — full definition (new state)

Offline has two distinct real causes that must produce the **same visual treatment**, so a user is
never left guessing which applies without opening the inspector:

1. **Unreachable** — the capability genuinely cannot be reached (a health check fails with no response)
   — this is the "something is wrong" reading and should escalate toward `Warning`/`Critical` treatment
   if it persists past a short grace window, rather than sitting indefinitely as a neutral gray tile.
2. **Not enabled for this tenant** — the vertical/module is real elsewhere on the platform but not
   turned on for this tenant (`ENTERPRISE_CITY.md` §22's tenant-conditional rendering rule). **This case
   should not render a building at all** — per the existing rule, a disabled vertical has no building,
   full stop. Offline-as-a-visible-dimmed-state is reserved for case 1 only (a real, enabled capability
   that is temporarily unreachable), never used to represent "you don't have this."

**Visual treatment:** desaturated/dimmed tile (reusing the existing `is-dimmed` opacity treatment from
`ENTERPRISE_CITY.md`'s overlay-filter mechanism, §20), a distinct "offline" silhouette state (no pulse,
no glow, flat), and — once past the grace window — an escalation to a `Warning`/`Critical` border tint
so a *persistent* outage is never silently indistinguishable from routine dimming.

## 4. User present — full definition (new state)

Directly extends `WORKSPACE_INTERACTIONS.md` §21 (Live presence) and §22 (Cursor sharing), which already
name Enterprise City as the primary use case:

- **A small presence indicator** (avatar stack, reusing the Avatar token treatment,
  `ENTERPRISE_DESIGN_SYSTEM.md` §2) renders on any building with one or more current viewers.
- **Ambient and non-blocking** — presence never locks a building or prevents another user's focus/click,
  identical to the general collaboration rule in `WORKSPACE_INTERACTIONS.md` §21.
- **Not a system-health signal.** Unlike every other state in this document, *User present* says
  nothing about whether the capability is healthy — a building can be simultaneously `Critical` and have
  three colleagues present looking at the problem together. This is why it is an overlay, not a point on
  the health scale (§1).
- **Vision only.** No presence infrastructure exists anywhere in the platform today
  (`WORKSPACE_INTERACTIONS.md` §0) — this state cannot ship before that infrastructure does.

## 5. Precedence and combination rules

Because *AI working* and *User present* are overlays, only the four "base" states
(Active/Warning/Offline/Busy) need a precedence order for the cases where more than one condition is
technically true at once:

```
Offline  >  Warning  >  Busy  >  Active
```

Read as: if a building is genuinely unreachable, that always wins the visual treatment regardless of
any other signal (an unreachable service's task queue depth is meaningless to report). Otherwise,
`Warning` wins over `Busy` — a building working hard *and* flagged for attention should read as
needing attention first, busy-ness second. `Active` is the default when nothing more specific applies.

Overlay rendering rule: the AI dot and the presence-avatar-stack render **simultaneously with, and
never replace,** whichever base state above is currently showing — a building's core silhouette/tint
communicates the base state; the two small overlay glyphs communicate the two orthogonal facts.

## 6. Visual encoding

Reuses the exact color tokens `ENTERPRISE_CITY.md`'s shipped CSS already defines — this document adds
no new color, only maps the two new states onto existing tokens plus one new neutral:

| State | Color token | Silhouette treatment | Badge |
|---|---|---|---|
| Active | `--eds-success` (border tint) | Normal, full opacity | None required |
| Warning | `--eds-warning` | Normal, full opacity | Notification count badge |
| Offline | `--eds-text-muted` / `--eds-border` (desaturated, new neutral pairing — no new hex value, reuses existing neutral tokens) | Flat, no pulse | "Offline" text label, never color-only |
| Busy | `--eds-info` | Normal, full opacity | Task-count badge |
| AI working (overlay) | `--eds-primary` (the existing `ec-ai-dot`) | Small pulsing dot overlay | None |
| User present (overlay) | Neutral avatar-stack chrome, not a state color | Avatar stack overlay, top corner | Viewer count once >1 |

**Rule inherited from `ENTERPRISE_CITY_ARCHITECTURE.md` §20:** color is never the only signal for any
state — every row above pairs its color with a distinct shape/silhouette/label, consistent with the
platform's existing "never rely on color alone" rule.

## 7. Transitions

Every state change is an animation trigger, detailed fully in `ENTERPRISE_CITY_ANIMATIONS.md` — this
document names which transitions exist, not their timing:

- Active ↔ Warning ↔ Busy ↔ Offline: a state-change flash (existing `edm-status-flash` mechanism,
  `ENTERPRISE_CITY.md` §19), extended to cover the Offline transition once built.
- AI working (on/off): the existing AI-dot pulse appears/disappears without a flash — it is a presence
  indicator, not an alert.
- User present (viewer joins/leaves): a designed new transition — the avatar stack should fade a new
  viewer in and fade a departing viewer out, never a hard pop, consistent with the platform's general
  "no jump cuts" motion instinct (`ENTERPRISE_DESIGN_SYSTEM.md` §5.1).

## 8. Accessibility

Every state in this document has a required text equivalent (already true for the four shipped states
via `CITY_STATE_LABELS`'s RU/UA/English labels, `ENTERPRISE_CITY.md` §4) — Offline and User present must
ship with the same three-locale label treatment before they ship visually, not after. The List View
(`ENTERPRISE_CITY_ARCHITECTURE.md` §20) renders every state as a text column/badge, identical
information to the map, satisfying `02_PRODUCT_PHILOSOPHY.md` principle 8 for this specific subsystem.

## 9. District and Enterprise rollups

A district or Enterprise node's aggregate state (`ENTERPRISE_CITY.md` §11's "an Enterprise node glows
under the same rules a building tile does") follows the same precedence order (§5) applied across its
member buildings: **if any member building is `Offline`, the rollup shows `Offline`-adjacent
treatment only if all/most members are offline** (a single offline building inside an otherwise healthy
district should not make the whole district read as down) — the precise rollup threshold (what fraction
of buildings must share a state before it propagates up) is an implementation detail left open, but the
**rule** that a rollup must never contradict what a user would see by looking at the individual
buildings is not — this is the same honesty constraint `02_PRODUCT_PHILOSOPHY.md` principle 9 applies at
every other level of this platform.

## Related documents

`ENTERPRISE_CITY_ARCHITECTURE.md` §4 (summary and cross-reference), `ENTERPRISE_CITY.md` §9 (the
shipped four-state implementation this extends), `ENTERPRISE_CITY_ANIMATIONS.md` (transition timing),
`WORKSPACE_INTERACTIONS.md` §20–§22 (the presence/collaboration substrate §4 depends on).
