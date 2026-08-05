# Enterprise City — Animation Specification

**Status:** permanent specification. Companion to `ENTERPRISE_CITY_ARCHITECTURE.md` §12. Documentation
only — no source code should be modified as a result of reading this. Every timing/easing value below
is a reference to the tokens already defined in `ENTERPRISE_DESIGN_SYSTEM.md` §9 — this document
defines no new duration or easing curve; it only maps City-specific triggers onto the existing shared
scale.

## 0. The one governing rule

**"Every animation represents a system event"** (`ENTERPRISE_CITY_ARCHITECTURE.md` §1) is a validation
rule, not a slogan: every row in the table below names the specific real event it represents. Any
future proposed City animation that cannot fill in that column truthfully should be rejected in review,
the same severity as a hardcoded color value under `ENTERPRISE_DESIGN_SYSTEM.md` §2's token rule.

## 1. Principles (inherited, restated for the City specifically)

1. Purposeful — answers "what changed?" or "what can I do?" (`ENTERPRISE_DESIGN_SYSTEM.md` §5.1).
2. Calm — no bounce, no endless decorative loops (`ENTERPRISE_CITY.md` §2.5's "meaningful-only" rule,
   the City's strictest reading of Motion Design Language anywhere in the platform).
3. Fast — micro-interactions ≤120ms, page/city enter ≤320ms, settle ≤400ms
   (`ENTERPRISE_DESIGN_SYSTEM.md` §9).
4. One shared timing scale — every entry below uses `--eds-motion-{instant,fast,normal,slow,settle}`
   and `--eds-ease{,-out,-in,-emphasized}`, never a City-invented value.
5. Reduce Motion first — every entry has a defined reduced-motion behavior (§9 below), decided at
   design time, not patched in afterward.

## 2. Shipped animations (real today, `ENTERPRISE_CITY.md` §19)

| Animation | Represents (event) | Trigger | Token |
|---|---|---|---|
| Soft page enter | User navigated to the City | Landing on `/enterprise-city` | `.edm-page-soft` (`--eds-motion-slow`, `ease-out`) |
| Focus breathe | A building is being inspected | Hover/keyboard-focus | `edm-breathe`, 2.4s |
| State-change flash | A building's real status just changed | Visual-state transition (`ENTERPRISE_CITY_STATES.md` §7) | `edm-status-flash`, `--eds-motion-settle` (400ms) |
| AI pulse | An AI agent is actively working here right now | `aiActive` becomes true | `edm-pulse-soft`, 1.6s infinite — the one sanctioned continuous loop, confined to the AI dot glyph only |
| Hover lift | Pointer is over an interactive building | Mouse hover | `translateY(-2px)` + shadow, `--eds-motion-fast` |
| Viewport pan/zoom | User is navigating the map | Pan-to or zoom control | `.ec-plane` transform, `--eds-motion-normal`, `ease-out` |
| Minimap dot transition | State/focus changed | Any state or focus change | `--eds-motion-fast` |

## 3. New animations this document specifies

| Animation | Represents (event) | Trigger | Token | Notes |
|---|---|---|---|---|
| Offline transition | A building just became unreachable, or just recovered | State change to/from `Offline` (`ENTERPRISE_CITY_STATES.md` §3) | `edm-status-flash` extended to the new state, `--eds-motion-settle` | Reuses the existing state-flash mechanism exactly — no new animation primitive |
| Presence join/leave | A colleague started or stopped viewing this building | Presence signal change (`ENTERPRISE_CITY_STATES.md` §4) | Fade in/out, `--eds-motion-normal`, `ease-out` for join / `ease-in` for leave | Never a hard pop — consistent with the platform's no-jump-cuts instinct |
| Day/Night transition | Real time crossed the tenant's day/night threshold, or the user manually toggled it | Time-based trigger or manual toggle (`ENTERPRISE_CITY_ARCHITECTURE.md` §17) | Cross-fade between the light/dark token sets, `--eds-motion-slow` | This is a token cross-fade, not a new lighting-simulation effect — it reuses the theme engine's existing light/dark values (§0) |
| Runtime/health ambient shift | Aggregate platform runtime health changed (`ENTERPRISE_CITY_ARCHITECTURE.md` §13) | Real telemetry change, polled on the existing cadence | Slow cross-fade of the ambient city-wide tint, `--eds-motion-slow` — **never** the fast/instant tier, since this is a background-awareness signal, not something requiring immediate attention | Explicitly excluded from the AI-pulse-style continuous-loop exception — this is a discrete state change, not an ambient loop |
| Weather-as-health-metaphor (conditional, §18 of Architecture doc) | Same event as the runtime ambient shift above — this is an alternate visual skin of the identical signal, not a separate animation | Same as above | Same as above | If built, must share the exact same trigger/timing as the ambient shift — two different visual treatments of one event, never two independent effects |
| Agent transit marker movement (3D vision) | A real orchestration event — an AI agent moving work from one building to another (`ENTERPRISE_CITY.md` §6, §13) | A `platform_orchestrator` task hand-off between two capabilities | Steady linear movement along the workflow-route path, `--eds-motion-normal`-scaled per-segment, never accelerating/decelerating for dramatic effect | The one sanctioned "traveling object" in the entire City, in either mode |
| Camera flight (3D vision) | User navigated between buildings/zoom levels | Building-to-building or zoom-level navigation (`ENTERPRISE_CITY.md` §13, §18) | `--eds-motion-normal`/`slow` scaled to distance, always skippable via instant-cut toggle | Never a separate "cinematic" timing scale — same budget as every 2D transition |
| Growth/materialization (3D vision, one-time) | A new building/Enterprise/district genuinely came online for this tenant | First-ever render of a newly-enabled capability | One-time only per tenant per object — never repeats on subsequent visits | `ENTERPRISE_CITY.md` §19 already specifies this; restated here for completeness of the animation table |

## 4. Explicitly forbidden (restated with City-specific examples)

Inherited from `ENTERPRISE_DESIGN_SYSTEM.md` §5.4 and `ENTERPRISE_CITY.md` §19, with concrete City
examples so a reviewer has a fast test to apply:

- **Buildings "flying" into place on ordinary load** — only the one-time growth/materialization
  animation (§3) is permitted, and only on genuine first appearance, never on a normal page refresh.
- **A constant ambient zoom/pulse across the whole map** — the runtime/health ambient shift (§3) is a
  discrete, slow cross-fade tied to a real change, never a continuous breathing effect on the whole
  city.
- **Idle bounce on any building** — no building animates while nothing about it has changed.
- **Decorative traffic or pedestrian simulation** — the agent transit marker (§3) is the only moving
  object permitted, and only because it represents a real, specific orchestration event.
- **Cosmetic/randomized weather** — explicitly rejected in `ENTERPRISE_CITY_ARCHITECTURE.md` §18; if
  weather is built at all, it is a re-skin of the health ambient shift, never an independent decorative
  system.
- **A "cinematic" camera timing scale distinct from the rest of the product** — camera flights (§3) use
  the same duration tokens as every other transition in the platform.

## 5. Reduced motion

Every animation in §2–§3 collapses under `prefers-reduced-motion: reduce` / `data-reduced-motion="true"`
exactly as `ENTERPRISE_DESIGN_SYSTEM.md` §5.5 already specifies platform-wide:

- Durations collapse toward `1ms`; the visual **end state still applies instantly** — a building whose
  state changed to `Warning` still shows the warning tint immediately, it simply arrives without the
  flash.
- The AI pulse and any future continuous-loop exception (§3's ambient shift is explicitly *not* one)
  are disabled outright under reduced motion, per the existing rule that the platform's one sanctioned
  loop still respects the user's motion preference.
- Camera flights (3D vision) become instant cuts — the skip-flight toggle from
  `ENTERPRISE_CITY_ARCHITECTURE.md` §13 becomes the *default* behavior under reduced motion, not an
  extra opt-in.
- Presence join/leave (§3) fades become instant appear/disappear — the *information* (who is present)
  must still convey with zero animation, since it is functionally informative, not decorative.

## 6. Timing reference (no new values — pointer only)

| Token | Value | Used for in this document |
|---|---|---|
| `--eds-motion-instant` | 80ms | (not directly used by City animations — reserved for press feedback elsewhere in the platform) |
| `--eds-motion-fast` | 120ms | Hover lift, minimap transitions |
| `--eds-motion-normal` | 200ms | Viewport pan/zoom, presence fade, per-segment camera flight |
| `--eds-motion-slow` | 320ms | Page enter, Day/Night cross-fade, health ambient shift, camera flight (longer distances) |
| `--eds-motion-settle` | 400ms | State-change flash (including the new Offline transition) |

Full definitions: `ENTERPRISE_DESIGN_SYSTEM.md` §9.

## Related documents

`ENTERPRISE_CITY_ARCHITECTURE.md` §12 (summary and cross-reference), `ENTERPRISE_CITY.md` §19 (the
shipped animation table this extends), `ENTERPRISE_CITY_STATES.md` §7 (the state transitions these
animations represent), `ENTERPRISE_DESIGN_SYSTEM.md` §5 and §9 (the motion canon this document inherits
in full).
