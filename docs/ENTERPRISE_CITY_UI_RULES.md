# Enterprise City — UI Composition Rules

**Status:** permanent specification. Companion to `ENTERPRISE_CITY_ARCHITECTURE.md` (primarily §2, §3,
§6, §10, §17, §20, §22). Documentation only — no source code should be modified as a result of reading
this. This document defines **composition rules** — how the City's UI is laid out and assembled from
existing tokens — never new token values; every color/spacing/typography value referenced here is
defined once in `ENTERPRISE_DESIGN_SYSTEM.md` and linked, not restated.

## 0. The one rule this whole document enforces

**The City is a consumer of the design system, never a second one.** Any City-specific UI need should
be satisfiable by composing existing tokens/components (`ENTERPRISE_DESIGN_SYSTEM.md` §§2–13); if it
genuinely cannot be, that is itself a signal worth raising against the design system, not a license to
invent a parallel City-only value.

## 1. City plane / coordinate system

- The 2D map plane uses a percentage-based coordinate space (`x, y, w, h` in 0–100), exactly as shipped
  (`ENTERPRISE_CITY.md` §9.1) — this document adds a **minimum tile size rule**: no building tile should
  render below roughly 8% width/height on any supported viewport, since below that threshold the
  silhouette (§3) and label become illegible, undermining `ENTERPRISE_CITY.md` §4's "legible without
  reading" principle.
- **Building spacing:** adjacent buildings within a district must maintain visible separation (the
  existing gap in shipped coordinates, e.g. Sales at x:28 vs. CRM at x:12, already demonstrates this) —
  a future building addition should not be placed so close to a neighbor that their tiles visually
  merge at default zoom.
- **District boundaries are implicit**, not drawn as hard lines — a district is communicated by its
  buildings' shared shape language (§2 below) and spatial clustering, never a rectangle/border drawn
  around a region, which would read as a decorative map feature rather than an organizational grouping.

## 2. District shape language

Reuses `ENTERPRISE_CITY.md` §2/§8 exactly — this is a composition rule, not a new definition:

| District | `border-radius` | Rule |
|---|---|---|
| Commerce | `0.65rem` | Applied uniformly to every building in the district |
| Ops | `0.35rem` | Applied uniformly |
| People | `1.1rem` | Applied uniformly |
| Intel | `0.5rem 0.95rem` | Applied uniformly |
| Hub | Default radius + 2px primary-tinted border | The one district whose buildings get a border-weight distinction, not just shape |

**Composition rule:** a building's district class is a CSS class applied to the tile, never an inline
override — this is what guarantees the "uniform within a district" rule can't quietly drift per
building over time.

## 3. Building tile composition

Every building tile is composed from the same fixed slot order, regardless of district or state:

```
┌─────────────────────────┐
│  [silhouette]            │  ← §7, top-center or top-left depending on tile size
│  [short label]            │  ← ENTERPRISE_DESIGN_SYSTEM.md §3's `.eds-type-label`-equivalent scale
│  [state label/badge]      │  ← ENTERPRISE_CITY_STATES.md §6, bottom
│  [AI dot, if aiActive]    │  ← small overlay, fixed corner position
│  [presence stack, if any] │  ← small overlay, opposite corner from AI dot
│  [notification badge]     │  ← small overlay, remaining corner
└─────────────────────────┘
```

**Rule:** overlay glyphs (AI dot, presence stack, notification badge) occupy fixed, non-competing
corners — a tile with all three active states simultaneously must never let one overlay obscure
another; if a future state addition can't fit this four-corner budget, that is a signal to redesign the
tile's information density, not to stack overlays.

## 4. Glass vs. solid — chrome boundary

Directly inherits `ENTERPRISE_DESIGN_SYSTEM.md` §6.1's rule, applied explicitly to every City surface:

| Surface | Treatment |
|---|---|
| Header/toolbar (search, overlay toggles, zoom controls, §9) | Glass chrome (backdrop-blur), per the platform's reserved chrome treatment |
| Building tiles | **Solid** (`--eds-surface`-derived), never glass — a building is content, not chrome |
| Minimap panel | Solid card, per the standard Card recipe (§8) |
| Inspector panel | Solid card |
| Floating windows (if a City detail is ever popped into one, `ENTERPRISE_NAVIGATION.md` §13) | Solid, per that document's rule that floating panels are content surfaces, not chrome |

**This boundary must never invert.** A future "make buildings feel more premium" request that proposes
glass-effect buildings should be declined on this rule alone — it would directly contradict the
platform-wide chrome/content distinction, not just a City-specific preference.

## 5. Typography

Reuses `ENTERPRISE_DESIGN_SYSTEM.md` §3 unchanged — no City-specific type scale:

| City element | Design system role |
|---|---|
| Building short label | `.eds-type-label` (0.8125rem, medium weight) |
| Building state text | `.eds-type-status` (0.75rem, semibold, tracked) — reused directly from `ENTERPRISE_CITY_STATES.md`'s existing state-label treatment |
| Inspector title | `.eds-type-title` |
| Inspector purpose one-liner | `.eds-type-helper` |
| District/section labels (e.g. minimap headers) | `.eds-type-section` (uppercase, tracked) |
| Header page title | `.eds-type-h1`/`.eds-type-h2` per `ENTERPRISE_DESIGN_SYSTEM.md` §3's page-title role |

## 6. Color and state mapping

Full detail lives in `ENTERPRISE_CITY_STATES.md` §6 — this document only restates the composition rule:
a state's color is always applied to the tile's **border**, never its fill background wholesale (fills
stay near-neutral `--eds-surface`-derived tones per §4), so text/silhouette contrast inside the tile
never depends on which state is active. This is what keeps every state legible without a separate
per-state text-color override.

## 7. Iconography / silhouette rules

Silhouettes follow the exact same construction discipline as the platform's icon library
(`ENTERPRISE_DESIGN_SYSTEM.md` §10) even though they're built from CSS shapes rather than SVG paths:

- **Line-based, not filled** — silhouettes use `border`/`box-shadow` outlines or a single
  `background: currentColor` clip-path shape, consistent with the icon library's stroke-only rule
  applied in spirit (a silhouette reads as an outline/glyph, never a solid photographic shape).
- **One glyph, one meaning, forever.** A silhouette shape, once assigned to a building, is never reused
  for an unrelated building — `ENTERPRISE_CITY.md` §4's "legible without reading" promise depends on
  this constancy holding indefinitely, not just at launch.
- **Sized on the same 1rem/1.15rem/0.85rem scale** already shipped (full tile vs. minimap-mini
  variants) — no third silhouette size is introduced by this document.

## 8. Minimap composition

- A minimap panel is a standard Card (`ENTERPRISE_DESIGN_SYSTEM.md` §13) titled per the platform's
  existing card-title convention, containing only state-colored dots at each building's tile center —
  no silhouettes, no labels, by design (the minimap's entire value is at-a-glance density, which
  per-building detail would undermine).
- **The current viewport/focus is indicated** on the minimap (a highlighted dot or, in the 3D vision, a
  camera-frustum outline per `ENTERPRISE_CITY.md` §15) — a minimap without a "you are here" marker fails
  the Google Maps quality bar this whole architecture is held to
  (`ENTERPRISE_CITY_ARCHITECTURE.md` §1).

## 9. Toolbar / header composition

The City's own in-page navigation chrome (`ENTERPRISE_CITY.md` §20) is composed left-to-right/top-to-
bottom in a fixed order, never rearranged per tenant/theme: page title block → glance chips → context
navigation strip → search + overlay toggles + zoom controls → legend. **Rule:** new toolbar controls are
added to this existing order at the most logically adjacent position (e.g., a future "List View" toggle,
`ENTERPRISE_CITY_ARCHITECTURE.md` §20, belongs beside the zoom controls as a third view-mode control,
not appended at the far end of an unrelated group).

## 10. Responsive rules

Inherits `ENTERPRISE_DESIGN_SYSTEM.md` §18 and `ENTERPRISE_CITY_ARCHITECTURE.md` §22 directly:

- **Mobile defaults to List View** (§20 of the Architecture doc) — the map becomes an explicit opt-in
  "Map View," not a cramped forced default.
- **Grid gutters and page padding contract on mobile** exactly as every other surface's do
  (`ENTERPRISE_DESIGN_SYSTEM.md` §18) — the City introduces no separate mobile breakpoint scale.
- **Toolbar controls collapse into an overflow affordance below the tablet breakpoint**, consistent
  with `.eds-toolbar`'s existing wrap behavior (`ENTERPRISE_DESIGN_SYSTEM.md` §12), rather than a
  City-specific mobile toolbar redesign.

## 11. Accessibility UI rules

- **Every building tile has a visible focus ring** on keyboard focus (§9 of the Architecture doc's
  Tab-cycling), using the platform's shared `.eds-focus-ring`/`--eds-shadow-focus` token — never a
  custom City focus treatment.
- **Minimum contrast** for state-border colors against the tile's near-neutral fill (§6) must meet
  WCAG AA, the platform's stated standard (`ENTERPRISE_DESIGN_SYSTEM.md` §1) — verified per theme
  (light/dark/corporate/custom, §17 of the Architecture doc), not just the default light theme.
- **The List View (§20 of the Architecture doc) uses the standard `DataGrid`/`Table` primitives**
  (`ENTERPRISE_DESIGN_SYSTEM.md` §13's catalog) with the same column set as the map's information
  (name, district, state, notifications, AI-active, present-users) — no information available on the
  map may be map-only.

## 12. List View composition (the accessible parallel surface)

- **Structured as a standard sortable/filterable table**, not a simplified/lesser version of the map's
  data — every column corresponds directly to a piece of information a building tile conveys (§3), so
  parity is verifiable column-by-column rather than asserted qualitatively.
- **Filters mirror the map's executive overlay toggles** (All/Health/Activity/AI,
  `ENTERPRISE_CITY.md` §20) as real column filters, not a separate filtering vocabulary.
- **Row click behaves exactly like tile click** (navigate to the real route) — the List View is a
  different rendering of the identical interaction model (`ENTERPRISE_CITY.md` §17), never a
  differently-behaved secondary feature.

## Related documents

`ENTERPRISE_CITY_ARCHITECTURE.md` (the document this composes rules for), `ENTERPRISE_CITY_STATES.md`
(state-to-color mapping this document's §6 references), `ENTERPRISE_CITY_ANIMATIONS.md` (motion applied
to the composition rules here), `ENTERPRISE_DESIGN_SYSTEM.md` (the sole source of every token value
referenced throughout this document).
