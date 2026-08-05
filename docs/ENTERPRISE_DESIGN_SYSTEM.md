# Enterprise Design System — The Visual Design Bible

**Status:** permanent, living engineering specification. **All future UI work on the Enterprise Web
Platform (`src/web`) must follow this document.** This is not a proposal — it consolidates and
supersedes the thin `ENTERPRISE_DESIGN_SYSTEM.md` stub, `EDS_GRID_ICONS_ANIMATION.md`, and the four
EP-series product-excellence specs (`EP_01_EXECUTIVE_EXPERIENCE.md`, `EP_02_ENTERPRISE_DESIGN_
LANGUAGE.md`, `EP_03_MOTION_DESIGN_LANGUAGE.md`, `EP_04_AI_PERSONALITY.md`) into one canonical
reference. Those source documents remain as historical sprint records; **this document is the one to
read and follow going forward**, and it should absorb the content of any future `EP_0N_*` visual/motion
spec rather than leaving the canon scattered across sprint files.

**Version lineage:** EDS `9.4.0` (tokens/architecture, unchanged since Sprint 26.2) · EDL `1.0`
(`ENTERPRISE_DESIGN_LANGUAGE`, EP-02) · MDL `1.0` (`MOTION_DESIGN_LANGUAGE`, EP-03) · Advisor `1.0`
(`AI_PERSONALITY_VERSION`, EP-04). **GA baseline:** this combined canon (EDL 1.0 + MDL 1.0 + Advisor
1.0) is the visual/motion/voice standard for Enterprise Platform v1.0 GA (EP-08).

**Implementation:** `src/web/design-system/` (tokens, colors, typography, icons, grid, spacing,
elevation, animation, responsive, accessibility, catalog, theme engine) + `src/web/design-system/
styles/{tokens,edl,motion}.css` + `src/web/src/ui/*` (composed primitives). Backend governance pairing:
`platform_enterprise_design_system/` library, `enterprise_hub.design_system` suite, API
`/api/enterprise-eds/v1`. CSS custom properties are prefixed `--eds-*`; Web Foundation aliases
`--ew-*` map onto the same tokens — never introduce a third prefix.

**Scope note — two frontends, one canon:** `platform_console` (the separate Enterprise Control Center
for the ADOS OS runtime, see `ARCHITECTURE_MAP.md` §6) uses its own dark-glass Tailwind theme
(`platform_console/src/index.css`) rather than importing `src/web/design-system`. That is an accepted,
contained exception for that one console — §6 below documents its treatment explicitly so it doesn't
silently drift, but **new UI anywhere in `src/web`, and any new enterprise-facing surface, follows this
document, not the console's ad hoc theme.**

---

## 1. Design philosophy

1. **Recognizable without a logo.** Every screen should read as one premium product through color,
   type, spacing, and tone alone — this is the explicit brand test from EP-02: *"Teal primary + IBM
   Plex + quiet uppercase section labels + soft executive cards = recognizable without logo."*
2. **Executive-first, not developer-first.** The primary user is a business owner/operator reading a
   dashboard in ~10 seconds (EP-01's Morning Brief mission), not an engineer inspecting a data grid.
   Default to calm, decision-oriented composition over dense tooling chrome.
3. **Motion explains, it doesn't entertain.** Per MDL's mission: *"Movement explains state — it does
   not entertain."* Every animation must answer "what changed?" or "what can I do?" — see §5.
4. **AI is an advisor, not a chatbot.** Per EP-04: the AI surfaces present as an **Executive Advisor** —
   calm, confident, concise, proactive — never a conversational toy. See §16.
5. **Extend tokens, never hardcode.** No raw hex/rem values in feature code when a token exists (EP-02
   rule: *"Never hardcode brand teal. Always use `--eds-primary`."*). This is enforced by convention,
   not a linter — treat any new hardcoded color/spacing value in a PR as a defect.
6. **No new Engine / Store / Runtime / AI Core for visual work.** Every EP-series sprint that shaped
   this canon was explicitly scoped as "composition + CSS only" over existing architecture
   (`CLAUDE.md`'s "prefer extension over replacement" applied to design work specifically). Visual
   polish work should never justify a new state store, backend engine, or data layer.
7. **Calm over decorative.** No bounce, no confetti, no autoplay carousels, no parallax, no continuous
   motion on static content. See the forbidden list in §5.4.
8. **One shared timing/easing scale for the whole product** — not per-component invented durations.
   See §9.
9. **Accessible by default, not by retrofit.** WCAG AA is the standard (`accessibilityManager.standard`
   in `src/web/design-system/accessibility/index.ts`), and `prefers-reduced-motion` is honored
   everywhere motion is used, not opted into per surface.

---

## 2. Visual language

- **Brand color:** teal primary (`#0f6a5a` light / `#3ecfad` dark / `#125b4a` corporate) paired with a
  navy/intel secondary (`#1f3a5f`). This pairing — not any single hex value — *is* the brand; it must
  survive every theme remap (§4).
- **Typeface:** IBM Plex Sans for UI text and display, IBM Plex Mono for code/monospace contexts,
  falling back to `"Segoe UI", sans-serif` / `ui-monospace, monospace`. No secondary UI typeface.
- **Surface treatment:** solid, token-bound surfaces by default (`--eds-surface`, `--eds-surface-
  raised`, `--eds-surface-sunken` via `color-mix`) — not glass. Glass is a deliberate, contained
  accent reserved for shell chrome only (§6), not a general surface treatment.
- **Shape:** soft rounded corners scaling with a component's weight in the hierarchy — small controls
  use `--eds-radius-md` (0.375rem), cards use `--eds-radius-xl` (0.75rem), "identity" hero surfaces
  (Morning Brief, Control Tower, Enterprise City hero, Concierge dock) use the largest
  `--eds-radius-2xl` (1rem) via a shared `--edl-identity-radius` token — bigger surfaces get bigger
  radii, consistently.
- **Iconography style:** minimal line icons, not filled/solid glyphs (§10).
- **Tone of voice:** quiet, uppercase section labels with wide letter-spacing for structural chrome
  (`.eds-type-section`), calm sentence-case body copy for content — never both loud at once.
- **Identity surfaces share a visual signature.** Morning Brief, AI Concierge dock, Control Tower/
  Mission Control, Enterprise City/Twin hero panels, and Marketplace/Builder strips all share
  `--edl-identity-radius` and `--edl-identity-border` (`color-mix(in oklab, var(--eds-primary) 22%,
  var(--eds-border))`) — this is what makes disparate executive surfaces read as one family.

---

## 3. Typography

Font stacks (`src/web/design-system/tokens/index.ts`):

```
sans / display:  "IBM Plex Sans", "Segoe UI", sans-serif
mono:            "IBM Plex Mono", ui-monospace, monospace
```

Type scale — size, weight, line-height, and **role** (not just a size name):

| Role | Class | Size | Weight | Line-height | Use |
|---|---|---|---|---|---|
| Display XL | `.eds-type-display-xl` | 3rem | 700 (bold) | 1.15 | Rare — marketing/first-time-user only |
| Display L | `.eds-type-display-l` | 2.25rem | 700 | 1.2 | Rare — marketing/FTUE only |
| Heading 1 | `.eds-type-h1` | 1.875rem | 600 (semibold) | 1.25 | Page titles |
| Heading 2 | `.eds-type-h2` | 1.5rem | 600 | 1.3 | Panel/section titles |
| Heading 3 | `.eds-type-h3` | 1.25rem | 600 | 1.35 | Sub-section titles |
| Heading 4 | `.eds-type-h4` | 1.125rem | 500 (medium) | 1.4 | Minor headings |
| Title | `.eds-type-title` | 1.25rem | 600 | 1.3, `-0.02em` tracking | Mid-weight page subsection |
| Section | `.eds-type-section` | 0.8125rem | 650 | uppercase, `+0.04em` tracking | Quiet structural/executive labels |
| Body Large | (token `bodyLarge`) | 1.125rem | 400 (regular) | 1.5 | Emphasized body copy |
| Body | `.eds-type-body` | 1rem | 400 | 1.5 | Default copy |
| Small | `.eds-type-small` | 0.875rem | 400 | 1.45 | Secondary copy |
| Caption | `.eds-type-caption` | 0.75rem | 400 | 1.4, muted color | Meta text |
| Helper | `.eds-type-helper` | 0.75rem | 400 | 1.4, muted color | Form help/hints |
| Label | `.eds-type-label` | 0.8125rem | 500 | 1.3 | Field/control labels |
| Button | `.eds-type-button` | 0.875rem | 500 | 1.2 | Control text |
| Status/Badge | `.eds-type-status` | 0.75rem | 600 | `+0.02em` tracking | Compact status indicators |
| Quiet label | `.eds-quiet-label` | 0.6875rem | 650 | uppercase, `+0.06em` tracking, muted | Smallest structural label |

**Rules:**
- Section labels are always uppercase + letter-spaced; **never use display sizes inside dense ops
  panels** (EP-02 rule) — display type is for rare hero moments only.
- Tables use 0.875rem with sticky headers (`.eds-table`); dialogs/drawers use 1.125rem semibold titles
  (`.eds-drawer-title`).
- KPI/numeric values use `font-variant-numeric: tabular-nums` with `-0.02em` tracking
  (`.eds-kpi-value` / `.edm-kpi`) so digits don't jitter horizontally as they update.

---

## 4. Colors

Full semantic palette (`src/web/design-system/tokens/index.ts` + `styles/tokens.css`):

| Role | Default | Soft | Hover | Active |
|---|---|---|---|---|
| Primary (brand) | `#0f6a5a` | `#d8efe9` | `#0c5649` | `#0a4a3f` |
| Secondary/Accent (navy/intel) | `#1f3a5f` | `#e4ebf5` | `#18304f` | `#14283f` |
| Success | `#027a48` | `#d1fadf` | — | — |
| Warning | `#b54708` | `#fef0c7` | — | — |
| Danger / Critical | `#b42318` | `#fee4e2` | — | — |
| Info | `#026aa2` | `#e0f2fe` | — | — |

Neutral scale (0–900): `#ffffff, #f8fafc, #f1f5f9, #e2e8f0, #cbd5e1, #94a3b8, #64748b, #475569,
#334155, #1e293b, #0f172a`.

Structural triads, per theme:

| Token | Light | Dark | Corporate |
|---|---|---|---|
| `--eds-bg` | `#f4f6f8` | `#0b1220` | `#f0f3f7` |
| `--eds-surface` | `#ffffff` | `#121a2a` | `#ffffff` |
| `--eds-border` | `#d7dee7` | `#243247` | `#c9d3df` |
| `--eds-text` | `#142033` | `#e8eef7` | `#101828` |
| `--eds-text-muted` | `#5b6b7c` | `#9aa8b8` | `#475467` |
| `--eds-text-disabled` | `#94a3b8` | (inherits) | (inherits) |
| `--eds-primary` | `#0f6a5a` | `#3ecfad` | `#125b4a` |
| `--eds-primary-soft` | `#d8efe9` | `#14352e` | `#d7ebe5` |

**Rules:**
- Themes are `light`, `dark`, `corporate`, and `custom` (`themeEngine.themes`, `applyTheme()` sets
  `data-theme`/`data-brand` on `<html>`). A `custom` theme with `BrandOverrides` (primary,
  primarySoft, font) can retint `--eds-primary`/`--eds-primary-soft`/`--eds-font-sans` per tenant
  without touching component code — **this is the sanctioned white-label mechanism.**
- `[data-contrast="high"]` forces `--eds-border: #000000` and collapses `--eds-text-muted` to
  `--eds-text` — support this state in any new color usage, don't assume only the 3 named themes exist.
- Badges use **soft semantic fills only** (`.eds-badge--{default,success,warning,danger,info}`) — never
  raw Tailwind color utilities (`emerald-500` etc.) as a shortcut; go through the soft tokens.
- Never hardcode `#0f766e` or any other literal brand hex in feature CSS — this was flagged and
  swept in EP-02 specifically because it breaks theme remapping.

---

## 5. Motion

**Mission (MDL 1.0):** *"Every user action is accompanied by clear, smooth, and functional animation.
Motion explains state — it does not entertain."*

### 5.1 Principles

1. **Purposeful** — motion answers "what changed?" or "what can I do?"
2. **Calm** — short durations; no bounce; no endless decorative loops on static content.
3. **Fast** — micro-interactions ≤120ms; page enter ≤320ms; settle ≤400ms.
4. **Shared timing** — one duration/easing scale for the whole product (§9) — never invent a
   per-component duration.
5. **Reduce Motion first** — `prefers-reduced-motion` and `data-reduced-motion="true"` disable motion
   while preserving layout; this is a first-class design constraint, not an afterthought pass.

### 5.2 Allowed patterns

| Pattern | Class | Scenario |
|---|---|---|
| Page enter | `.edm-page` | Route content, keyed by pathname |
| Soft enter | `.edm-page-soft` | Secondary shells (e.g. Enterprise City) |
| Stagger | `.edm-stagger` | Brief columns, KPI grids, suggestion lists (max ~8 items, 40ms apart) |
| Card enter / refresh | `.edm-card-enter` / `.edm-card-refresh` | New data snapshot / data refresh |
| Expand / collapse | `.edm-card-expand` / `.edm-card-collapse` | Ops strips, disclosure panels |
| Skeleton | `.edm-skeleton` | Loading placeholders (shimmer, 1.2s linear infinite) |
| Stream | `.edm-stream-bar` | Analyzing/streaming state |
| Refreshing overlay | `.edm-refreshing` | Soft overlay during refetch |
| Partial / background update | `.edm-partial-update` / `.edm-bg-update` | Live deltas (background pulse is *restricted* — see forbidden list) |
| AI live / analyzing | `.edm-ai-live` / `.edm-ai-analyzing` | Concierge dock idle-breathe / active-analysis states |
| AI suggest | `.edm-ai-suggest` | Recommendation rows entering/hovering |
| AI done | `.edm-ai-done` | Task completion confirmation |
| KPI | `.edm-kpi` | Tabular numeric values + update tick |
| Overlay / drawer | `.edm-overlay-panel`, drawer CSS | Modal, command palette, auth |
| Toast / notify | `.edm-toast` / `.edm-notify-enter` | Transient feedback |
| Palette item | `.edm-palette-item` | Command palette / search result rows |
| Press | `.edm-press`, button `:active` | Universal press-down microinteraction |

### 5.3 Surface map

| Scenario | Motion treatment |
|---|---|
| Login | Auth panel `.edm-overlay-panel` |
| Dashboard / Morning Brief | Brief enter + staggered columns/KPIs |
| Mission Control / Control Tower | Page enter + card hover/press only |
| Enterprise City | Soft enter; focus "breathe"; status flash; AI dot pulse — **and nothing else** |
| AI Concierge | Live breathe / analyzing stream / staggered suggestions |
| Marketplace / Builder / Twin | Shared page enter + card recipes |
| Settings / Profile | Control focus + page enter only |
| Search / Command Palette | Overlay scale + palette item press |

### 5.4 Forbidden

- Bounce / springy overshoot on any enterprise surface.
- Full-page spin loaders as primary chrome.
- Parallax scroll or autoplay carousels.
- Continuous motion on static text blocks.
- Any motion that blocks interaction for more than 400ms.
- Enterprise City "attraction" loops (buildings flying, constant zoom pulse) — City motion is
  **meaningful-only**: focus breathe, state-change flash, AI-dot pulse, nothing ambient.
- Confetti or novelty animations of any kind.

### 5.5 Accessibility

- `@media (prefers-reduced-motion: reduce)` collapses every duration token to `1ms` and disables
  named animations/transforms outright (see `motion.css`'s reduce-motion block for the exact
  selector list to extend when adding a new animated class).
- `[data-reduced-motion="true"]` mirrors the same behavior for an in-app user preference, independent
  of OS settings.
- Loading/streaming states must remain **visible without motion** (static bars/opacity change) — never
  rely on animation alone to communicate a loading state.
- Focus rings are never removed by reduced motion — only the transition *duration* collapses.

---

## 6. Glass effects

There are two distinct, deliberately-scoped glass treatments in this platform. **Do not blend them.**

### 6.1 EDS chrome glass (`src/web` — the canonical treatment)

Reserved for **shell chrome only** (header, sidebar) — never for content cards or dashboard widgets:

```css
.ews-glass {
  background: <surface color>;
  backdrop-filter: blur(16px) saturate(1.15);
  -webkit-backdrop-filter: blur(16px) saturate(1.15);
  box-shadow: 0 8px 28px color-mix(in oklab, #0b1220 8%, transparent);
}
```

Applied to `.ews-header.ews-glass` and `.ews-sidebar.ews-glass` (`src/web/src/shell/enterprise/
enterpriseShell.css`, Sprint 27.1 "Application Shell glass chrome"). Content underneath — cards,
tables, dialogs — stays on **solid** `--eds-surface`/`--eds-surface-raised`/`--eds-surface-sunken`
(§2). Glass is a chrome accent that signals "this is fixed navigation floating above content," not a
general aesthetic. A mobile drawer variant carries a directional shadow instead of blur:
`box-shadow: -12px 0 32px color-mix(in oklab, #0b1220 18%, transparent)`.

### 6.2 ADOS Console glass (`platform_console` — contained exception)

`platform_console` (the separate Enterprise Control Center for the ADOS OS TS kernel, see
`ARCHITECTURE_MAP.md` §6) uses a pervasive dark-glass aesthetic across nearly every panel:

```css
:root { color-scheme: dark; --bg-elevated: rgba(15, 23, 42, 0.72); --glow: 0 0 40px rgba(56, 189, 248, 0.12); }
.glass {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  backdrop-filter: blur(16px);
  box-shadow: var(--glow);
}
```

This is a dark-first, neon-accent (`--accent: #38bdf8` sky, `--accent-2: #818cf8` indigo) treatment
applied to essentially every `<section>`/`<div>` in that console, not just chrome. **This is an
accepted exception scoped to `platform_console` alone** — it renders a genuinely different product
(an ops console for an AI agent runtime, not the business-facing Enterprise Web Platform) and predates
this canon's chrome-only glass rule. Do not import this pattern into `src/web`, and do not spread
`.glass` further inside `platform_console` without deciding it's the intended direction for that app —
treat any expansion as a decision worth a line in that sprint's `RESULT.md`.

---

## 7. Depth

Elevation is expressed through **shadow + z-index pairing**, not blur or scale, except where glass
chrome (§6.1) explicitly layers blur on top:

| Level | Shadow | z-index | Use |
|---|---|---|---|
| `flat` | none | 0 (base) | Inline content, no separation from page |
| `raised` | `shadows.sm` | 0 (base) | Cards at rest |
| `overlay` | `shadows.md` | 20 (dropdown) | Dropdowns, popovers |
| `modal` | `shadows.lg` | 50 (modal) | Dialogs, modals |
| `focus` | `shadows.focus` | 0 (base) | Focus ring (not a stacking concern, a visibility one) |

Full z-index scale (`tokens.zIndex`): `base 0 → dropdown 20 → sticky 30 → drawer 40 → modal 50 →
toast 60 → tooltip 70`. **Never invent a new z-index value outside this scale** — if a new layer type
is needed, add it to the scale at the correct relative position rather than picking an arbitrary number.

Surface depth without shadows uses `color-mix`-derived raised/sunken variants rather than opacity
tricks:

```css
--eds-surface-raised: color-mix(in oklab, var(--eds-surface) 92%, var(--eds-primary) 4%);
--eds-surface-sunken: color-mix(in oklab, var(--eds-bg) 88%, var(--eds-border) 12%);
```

(Dark theme remaps the mix ratios, not the mechanism: `92%→90%` for raised, and sunken becomes a flat
`#0a101c` rather than a mix, since the dark background is already near the mix floor.)

---

## 8. Shadows

Canonical shadow scale (`tokens.shadows`, `styles/tokens.css`):

| Token | Value | Use |
|---|---|---|
| `none` | `none` | Flat elements |
| `sm` | `0 1px 2px rgba(15, 23, 42, 0.06)` | Cards at rest |
| `md` | `0 4px 12px rgba(15, 23, 42, 0.08)` | Hover state, dropdowns |
| `lg` | `0 12px 28px rgba(15, 23, 42, 0.12)` | Modals, drawers |
| `focus` | `0 0 0 3px rgba(15, 106, 90, 0.35)` | Focus ring (tinted with primary, not neutral) |

**Rule:** shadows scale with elevation level, not with arbitrary "how important is this" judgment —
use the `elevationSystem` mapping in §7, don't hand-pick a shadow value per component. Interactive
cards additionally get a **translateY(-1px) lift** on hover (`--edm-lift`) paired with the shadow
transition — depth is communicated by shadow *and* position together, not shadow alone.

---

## 9. Animation timing

The single shared duration/easing scale — **do not introduce a new duration value anywhere in the
product**; pick the closest existing token:

| Token | Value | Use |
|---|---|---|
| `--eds-motion-instant` | 80ms | Press feedback, palette-item highlight |
| `--eds-motion-fast` | 120ms | Hover, border, control focus |
| `--eds-motion-normal` | 200ms | Cards, lists, dialogs |
| `--eds-motion-slow` | 320ms | Page enter, Morning Brief entrance |
| `--eds-motion-settle` | 400ms | Status flash, partial-update confirmation |
| `--eds-stagger` | 40ms | Per-item delay in list/column cascades |

Easing curves:

| Token | Curve | Use |
|---|---|---|
| `--eds-ease` | `cubic-bezier(0.2, 0.8, 0.2, 1)` | Default for most transitions |
| `--eds-ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | Entrances |
| `--eds-ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | Exits (used rarely — most UI in this system doesn't animate exits) |
| `--eds-ease-emphasized` | `cubic-bezier(0.2, 0, 0, 1)` | Emphasis moments |

Press/scale constants: `--edm-lift: -1px` (hover lift on interactive cards/buttons), `--edm-press:
0.98` (scale-down on `:active`). In `prefers-reduced-motion: reduce`, every duration token collapses
to `1ms` and stagger to `0ms` — components should read duration/easing from these tokens (or their CSS
custom-property equivalents), never hardcode a millisecond value, so this collapse works automatically.

---

## 10. Iconography

Icon library (`src/web/design-system/icons/index.tsx`) — 11 named icons today: `navigation`, `ai`,
`crm`, `erp`, `finance`, `hr`, `analytics`, `notifications`, `security`, `settings`, `workflow`,
accessed via `<Icon name="..." />` or the `iconLibrary` map directly.

**Style contract** (every icon shares this exact `Base` wrapper):
- `viewBox="0 0 24 24"`, `fill="none"`, `stroke="currentColor"`, `strokeWidth="1.8"`,
  `strokeLinecap="round"`, `strokeLinejoin="round"`, `aria-hidden="true"`.
- Line icons only — no filled/solid glyph style, ever, in this system.
- Default render size `20px`; sizing otherwise goes through the icon size tokens below, not a raw
  `size` prop value chosen ad hoc.

Sizing tokens (`--eds-icon-{sm,md,lg}` / `.eds-icon--{sm,lg}`):

| Size | Token | Value |
|---|---|---|
| sm | `--eds-icon-sm` | 1rem |
| md (default) | `--eds-icon-md` | 1.25rem |
| lg | `--eds-icon-lg` | 1.5rem |

Color modifiers: `.eds-icon--muted` (muted text color), `.eds-icon--brand` (primary color).

**Rule:** prefer the EDS icon library over ad hoc SVGs or emoji as primary chrome — EP-02 explicitly
flagged leftover emoji-as-chrome as a defect to sweep, and it remains an open item
(`docs/EP_02_ENTERPRISE_DESIGN_LANGUAGE.md` §"Recommendations for EP-03+", item 3). When a needed icon
doesn't exist yet, add it to `iconLibrary` following the exact `Base` stroke contract above rather than
introducing a one-off icon component.

---

## 11. Layout grids

12-column grid system (`src/web/design-system/grid/index.ts`):

```
columns: 12
gutters: { mobile: 1rem, tablet: 1.25rem, desktop: 1.5rem }
containers: { fluid: 100%, fixed: { sm: 640px, md: 768px, lg: 1024px, xl: 1280px } }
```

Grid variants (`.eds-grid` base + modifier):

| Variant | Class | `grid-template-columns` | Use |
|---|---|---|---|
| Responsive | `.eds-grid--responsive` | `repeat(12, minmax(0, 1fr))` | General 12-col layout |
| Dashboard | `.eds-grid--dashboard` | `repeat(auto-fit, minmax(16rem, 1fr))` | Widget/card grids that reflow by available width, not a fixed column count |
| Workspace | `.eds-grid--workspace` | `minmax(14rem, 18rem) minmax(0, 1fr)` | Sidebar + content split (workspace shell) |

All variants share `gap: var(--eds-space-4)` (1rem) as the base grid gap.

---

## 12. Component spacing

Canonical spacing scale, 4px base (`tokens.spacing`, `spacingSystem.scale`):

```
0, 1(0.25rem), 2(0.5rem), 3(0.75rem), 4(1rem), 5(1.25rem), 6(1.5rem), 8(2rem), 10(2.5rem), 12(3rem), 16(4rem)
```

Contextual spacing tokens (`edl.css`) — **use these, not raw scale values, for layout rhythm**:

| Context | Token | Resolves to |
|---|---|---|
| Page padding | `--eds-page-pad` | `--eds-space-6` (1.5rem); `--eds-space-4` on mobile (<768px) |
| Section gap | `--eds-section-gap` | `--eds-space-6`; `--eds-space-4` on mobile |
| Card padding | `--eds-card-pad` | `--eds-space-4` |
| Card internal gap | `--eds-card-gap` | `--eds-space-3` |
| Toolbar gap | `--eds-toolbar-gap` | `--eds-space-2` |
| Dialog padding | `--eds-dialog-pad` | `--eds-space-6` |
| Drawer padding | `--eds-drawer-pad` | `--eds-space-5` |
| Control height (default) | `--eds-control-h` | 2.5rem |
| Control height (sm) | `--eds-control-h-sm` | 2rem |
| Control height (lg) | `--eds-control-h-lg` | 2.75rem |

**Rule (EP-02):** *"No one-off rem values for layout rhythm when a token exists."* If you find yourself
writing `margin-top: 1.3rem`, that's a signal to either use the nearest scale value or add a named
contextual token — not to keep the arbitrary value.

---

## 13. Card system

The card is the primary content unit of the platform — every dashboard, workspace, and identity
surface is built from this one recipe (`.eds-card` + React `Card`), not a bespoke panel per feature.

**Anatomy:**

```
.eds-card
├── .eds-card__header    (flex, space-between; title + optional status)
├── .eds-card__title     (uppercase, muted, 0.8125rem — same voice as .eds-type-section)
├── .eds-card__body      (flex: 1, min-width: 0)
└── .eds-card__actions   (flex-wrap toolbar row)
```

Base recipe: `border-radius: var(--eds-radius-xl)`, 1px `--eds-border`, `--eds-surface` background,
`shadows.sm` at rest, `shadows.md` + tinted border on hover
(`color-mix(in oklab, var(--eds-primary) 28%, var(--eds-border))`).

**States** (all via prop → class, not separate components):

| State | Prop | Class | Effect |
|---|---|---|---|
| Loading | `loading` | `.is-loading` | `opacity: 0.72`, `pointer-events: none` |
| Empty | `empty` | `.is-empty` | Dashed border, sunken surface background |
| Success | `success` | `.is-success` | Border tinted toward `--eds-success` |
| Interactive | `interactive` | `.eds-card--interactive` | `cursor: pointer`, hover lift (`translateY(-1px)`) |
| Raised | `raised` | `.eds-card--raised` | Background swaps to `--eds-surface-raised` |

**Rules:**
- Never build a new "panel" component that duplicates this anatomy — extend `Card`'s props instead.
- Identity surfaces (Morning Brief, Concierge dock, Control Tower, Twin/City hero, Marketplace/Builder
  strips) additionally apply `--edl-identity-radius`/`--edl-identity-border` on top of the base card
  recipe — they are cards with a shared identity accent, not a different component.
- Card enter/refresh motion (`.edm-card-enter`, `.edm-card-refresh`) is the only sanctioned way to
  signal "this card just got new data" — see §5.

---

## 14. Dashboard principles

Per EP-01's Morning Brief redesign — the dashboard is the executive's morning briefing, not a data
dump:

1. **Brief-first hierarchy.** The Morning Brief composition (`ExecutiveMorningBrief` /
   `deriveMorningBrief`) leads the page; detailed enterprise-intelligence (EI) panels are collapsed
   by default, not competing for attention above the fold.
2. **What / Why / Next pattern.** Brief cards, KPI cards, health cards, activity cards, and
   recommendation cards all follow the same three-part (extended to four-part with AI cards, see §16)
   structure — a reader should never have to infer *why* a number is shown.
3. **~10-second comprehension target.** The explicit design target (EP-01 mission) is that a reader
   understands "what's happening, what needs attention, what AI suggests, and what's risk/opportunity"
   within about ten seconds of landing.
4. **Decision flow, not exploration flow.** Quick Actions route directly to Control Tower / Mission
   Control / Concierge / Twin / City — the dashboard is a dispatch point to deeper tools, not a place
   that tries to contain every feature itself.
5. **Stagger, don't dump.** KPI grids and brief columns enter via `.edm-stagger` (§5) rather than
   appearing all at once — this reinforces reading order without adding real latency (40ms/item).
6. **Health-aware ordering.** When system/business health is degraded, attention-worthy items reorder
   to the front (shared mechanism with the AI Advisor's suggestion reordering, §16.4) — the dashboard
   actively surfaces what's wrong rather than presenting a static, always-identical layout.
7. **Tabular KPI values.** Numeric KPIs always use `font-variant-numeric: tabular-nums` so live updates
   don't cause horizontal jitter (§3, §12).
8. **Use the dashboard grid variant, not the general 12-column grid** (`.eds-grid--dashboard`, §11) —
   dashboards reflow by widget width, they don't lock to a fixed column count.

---

## 15. Workspace principles

Per the Enterprise Workspace & Dashboard Framework (`src/web/workspace/`, backed by
`platform_enterprise_workspace/`):

1. **The workspace is the post-login home** — not the dashboard. A user lands in their personalized
   workspace, from which the executive dashboard is one destination among widgets/quick-actions, not
   the forced entry point for every role.
2. **Composed of five governed subsystems**, each with its own readiness contract: Dashboard Engine,
   Widget Library, Layout Manager, Search Center, Personalization (+ Realtime updates layered across
   all of them). New workspace features extend one of these five, not a sixth parallel concept.
3. **Widgets, not bespoke pages.** Workspace content is built from the shared widget library
   (backed by the card system, §13) — a new workspace capability should ship as a widget, reusing
   `.eds-grid--workspace`'s sidebar+content split (§11), not a standalone route with its own layout.
4. **Personalization is layout-level, not theme-level.** Per-user customization (widget arrangement,
   pinned items, layout choice) is the sanctioned personalization axis; per-user *theme* overrides are
   not — themes are a tenant/brand concern (§4), not an individual-user one.
5. **Realtime is a cross-cutting layer**, not a per-widget feature to reimplement — new widgets should
   subscribe to the existing realtime update mechanism rather than polling independently.

---

## 16. AI interaction design

Per EP-04's mission: *"Make the AI a natural helper to the business owner — an Executive Advisor, not
a chatbot."*

### 16.1 Enterprise tone (`ENTERPRISE_AI_TONE`, `aiPersonality.ts`)

| Trait | Rule |
|---|---|
| Calm | No hype, no emoji spam |
| Confident | Direct statements — avoid "maybe you could…" hedging |
| Businesslike | Decision language, not chat banter |
| Concise | Observation → Why → Action → Impact, and nothing longer |
| Proactive | Surface the next decision without waiting to be asked to "chat" |
| Respectful | Owner-first phrasing; never infantilizing copy |

### 16.2 Recommendation structure

Every AI recommendation, on every surface (Concierge dock, Morning Brief cards, live
`AiRecommendationsPanel`), uses the same four-part structure:

1. **Observation** — what is true right now.
2. **Why it matters** — the consequence for the owner.
3. **Suggested action** — a verb + destination, not a vague nudge.
4. **Expected impact** — a measurable or operational outcome.

### 16.3 Confidence — one badge, never a progress bar

| Level | Chip label | Use |
|---|---|---|
| High | "High" | Health, overdue items, today/at-risk items |
| Medium | "Likely" | Default insights |
| Low | "Explore" | Speculative/low-signal suggestions |

**Rule:** exactly one confidence badge per recommendation — never a numeric percentage, never a
progress-bar-style confidence visualization ("never a progress bar circus," per EP-04).

### 16.4 Context awareness

AI copy binds to live context (`advisorContextLine`): current section, company name, health ratio,
unread count, AI busy state. Suggestions **reorder toward attention items when health is degraded** —
the same reordering principle used by the dashboard (§14.6). A knowledge-awareness hint persists across
this reordering so the advisor doesn't appear to have "forgotten" prior context.

### 16.5 Session-scoped conversation memory

- Seen recommendations are marked (`markAdvisorSeen`) and filtered out for the rest of the browser
  session (`filterAdvisorSeen`) — the advisor should not repeat itself within a session.
- A minimum of 2 suggestions is always kept visible so the dock never goes empty.
- This memory is `sessionStorage`-scoped by design — **do not promote it to a persistent store**; that
  would be new state-layer scope beyond what an AI-presentation feature should require.

### 16.6 Language policy

| Surface | Policy |
|---|---|
| Dashboard owner status | English (badges, greetings, Brief status) |
| Enterprise City | RU/UA localization retained on City chrome specifically |
| Workspace | Organization's configured language for module work |
| Concierge Advisor | Calm English decision voice; confidence chips always English |

### 16.7 AI-specific motion

Reuses the shared motion system (§5), not a separate AI-only timing scale: `.edm-ai-live` (idle
breathe, 2.8s infinite — the one sanctioned "ambient" loop, reserved for AI presence indication only),
`.edm-ai-analyzing` (active streaming bar), `.edm-ai-suggest` (staggered slide-in for suggestion rows),
`.edm-ai-done` (completion confirmation).

---

## 17. Enterprise navigation

Architecture (three-layer, per `docs/ENTERPRISE_NAVIGATION.md`):

```
platform_enterprise_navigation/          # backend library
applications/enterprise_hub/navigation/  # hub suite + API (/api/enterprise-navigation/v1)
src/web/navigation/                      # React UI
```

**Principles:**

1. **Every module, application, vertical, AI agent, and workflow is instantly discoverable** through
   one unified navigation surface — new features register into this system rather than inventing a
   parallel nav entry point.
2. **Application registry is automatic**, not hand-maintained per feature — each registered app
   carries icon, name, status, owner, permissions, version, health, and last-update, scoped across
   Personal · Organization · Department · Project · Customer · AI · Temporary categories.
3. **Multiple discovery paths, one underlying registry:** global fuzzy search, smart favorites, recent
   history, breadcrumbs, and a Quick Switcher (`Ctrl+Tab`) all read from the same application registry
   — don't build a feature-specific search index when the global one exists.
4. **Workspace federation.** Navigation spans federated workspaces (switchable via `/workspaces/
   switch`), not a single flat menu — RBAC, workspace isolation, tenant isolation, and organization
   isolation are enforced at this layer (`docs/ENTERPRISE_NAVIGATION.md` "Security").
5. **Navigation chrome uses the sidebar/top-nav card components and the chrome-glass treatment**
   (`.ews-header.ews-glass`, `.ews-sidebar.ews-glass`, §6.1) — content it routes to stays on solid
   surfaces.
6. **Breadcrumbs are dynamic, not route-config strings** — they reflect the live application registry
   entry, so a renamed/moved feature doesn't require a separate breadcrumb-string update.
7. **Command Palette / global search shares overlay motion and palette-item press** (§5.2) with every
   other overlay surface in the product — it is not a bespoke modal.

---

## 18. Responsive behavior

Breakpoints (`tokens.breakpoints`, `responsiveEngine`):

| Viewport | Min-width |
|---|---|
| `mobile` | 0 |
| `tablet` | 768px |
| `laptop` | 1024px |
| `desktop` | 1280px |

`responsiveEngine.resolve(width)` returns the active viewport name; media queries are `(min-width:
<breakpoint>px)` — **mobile-first**, not desktop-first overrides.

**Rules:**

1. **Grid gutters scale with viewport**, not just column count: `1rem` (mobile) → `1.25rem` (tablet) →
   `1.5rem` (desktop) — see §11.
2. **Page/section padding contracts on mobile**: `--eds-page-pad` and `--eds-section-gap` drop from
   `--eds-space-6` to `--eds-space-4` below 768px — this is a token-level media query
   (`edl.css`), not a per-page override.
3. **Fixed container widths** exist for `sm`/`md`/`lg`/`xl` (640/768/1024/1280px) alongside a `fluid`
   (100%) option — pick the narrowest fixed width that fits the content's reading measure; don't
   default to fluid for text-heavy panels.
4. **The workspace grid's sidebar collapses**, not shrinks, below the point where `minmax(14rem,
   18rem)` no longer fits — a drawer take-over (with the directional shadow noted in §6.1) is the
   sanctioned mobile pattern for the workspace shell, not a squeezed sidebar.
5. **Reduced-motion and responsive behavior compose independently** — a mobile viewport does not imply
   reduced motion, and vice versa; both conditions must be handled, and neither should assume the
   other.

---

## Maintenance

This document absorbs future visual/motion/AI-voice specs rather than leaving them as separate
sprint-numbered files competing for authority. When a new `EP_0N_*` design sprint lands:

1. Update the relevant section(s) above with the new rules/tokens.
2. Bump the version lineage line at the top of this document.
3. Leave the original `EP_0N_*.md` in `docs/` as the historical sprint record (self-assessment scores,
   file-change inventory) — but this file is what a future contributor should be pointed to for "how
   do I build UI here," not the sprint record.
4. Cross-reference from `CLAUDE.md`'s sprint-closeout rule: a sprint that changes visual language is
   not done until this document reflects it.

## Related documents

- `docs/EP_01_EXECUTIVE_EXPERIENCE.md` … `EP_04_AI_PERSONALITY.md` — the sprint records this canon
  consolidates.
- `docs/EDS_GRID_ICONS_ANIMATION.md`, `docs/ENTERPRISE_NAVIGATION.md`, `docs/ENTERPRISE_WORKSPACE.md`
  — prior subsystem-specific docs, now folded in above.
- `ARCHITECTURE_MAP.md` §6, §11 — why `platform_console` sits outside this canon (§6.2 above).
- `MODULES.md` — catalog entry for `src/web` and the `design-system` implementation.
- `CLAUDE.md` — the broader engineering handbook this design bible operates under.
