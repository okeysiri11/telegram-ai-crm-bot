# Component Library Standard

**Status:** permanent standard. Documentation only — no source code was modified to produce this
document. Defines folder structure, reusable UI patterns, and the per-category standards
(Window/Dock/Command Palette, Dialogs, Forms, Tables, Dashboards) every feature area should follow.
Governed by `DESIGN_SYSTEM_GOVERNANCE.md`; every value/token referenced below is defined once in
`ENTERPRISE_DESIGN_SYSTEM.md` and linked, never restated.

## 1. Folder structure standard

**Problem this section fixes:** the audit behind `DESIGN_SYSTEM_GOVERNANCE.md` §2.3 found five feature
folders (`enterprise-city`, `enterprise-desktop`, `ai-production-studio`, `enterprise-governance`,
`enterprise-okr`) with five different internal shapes — some using a Zustand store, some a pure derive
function, some with a summary `Strip`, some without. Only the `index.ts` barrel was consistent
everywhere.

**Standard shape for a new feature folder**, chosen from what already works well in at least one real
folder rather than invented from nothing:

```
src/web/src/<feature-name>/
├── <feature>Catalog.ts     # static data/config for this feature (buildings, studios, districts, ...)
├── <feature>Store.ts        # Zustand store, only if the feature has real client-side mutable state
│   — or —
├── derive<Feature>.ts       # pure derive function, only if the feature is read-only over shared data
├── <Feature>Page.tsx        # the routed entry component — every feature folder gets exactly one
├── <Feature>Strip.tsx       # optional compact summary (§2) — only if this feature needs a Dashboard/
│                             #   Desktop-widget-sized representation of itself
├── types.ts                 # exported types, if not already folded into Catalog/derive files
└── index.ts                 # barrel export — required, every folder already has one
```

**Rule:** a feature folder picks *either* a Store *or* a derive function, never both, and states which
in its own top-of-file comment (several real files already do this, e.g. `cityEngine.ts`'s "presentation
camera controller, not a business runtime" framing) — the choice signals whether the feature owns
mutable state or only reads/reshapes shared state, which matters for a future contributor deciding where
a new piece of related state belongs.

## 2. Reusable UI patterns

### 2.1 The Strip — formalized as a real, shared primitive (currently missing)

**Problem:** twelve real components (`GovernanceStrip`, `MarketplaceStrip`, `OkrStrip`,
`AIBuilderStudioStrip`, `ControlTowerStrip`, `DataFabricStrip`, `IntegrationHubStrip`,
`EnterpriseTwinStrip`, `LearningStrip`, `AutonomyStrip`, `AIRuntimeStrip`, `PredictiveStrip`) all
render the identical anatomy with no shared component (`DESIGN_SYSTEM_GOVERNANCE.md` §2.1).

**Standard, extracted from what these twelve already agree on:**

```
<Strip aria-label="...">
  <StripLabel>{label}</StripLabel>
  <StripBadges>{badge, badge, ...}</StripBadges>
  <StripLink to={route}>{linkText}</StripLink>
</Strip>
```

A Strip is: a single labeled row, one or more real `Badge` components (never raw text standing in for
one), and exactly one trailing navigation link using the real `Button`/`Link` primitive (never a raw
`className="eds-type-small text-[var(--eds-primary)]"` span, which is what all twelve currently do
instead). **This component should be built once in `src/web/src/ui/Strip.tsx`** and every one of the
twelve existing implementations migrated to use it, passing feature-specific label/badges/link as
props — collapsing twelve bespoke CSS classes (`gov-strip`, `mkt-strip`, etc.) into one.

**`EnterpriseMetricsStrip.tsx` is not this pattern** — it is a KPI dashboard grid (§5) that happens to
share the word "Strip" in its name; it should not be migrated onto the `Strip` primitive above, and its
name is flagged in `UI_NAMING_CONVENTIONS.md` as a naming collision worth resolving separately.

### 2.2 The Card — real, mostly-consistent, with one known gap

The real `Card` component (`src/web/src/ui/`) is used correctly in most audited feature areas. The one
gap: `ews-glass` (a chrome-scoped CSS class) is used as a substitute card surface in five files
(`DESIGN_SYSTEM_GOVERNANCE.md` §2.1) instead of `Card`. **Standard:** any surface that visually reads as
a card — bordered, padded, containing a title and body — uses the real `Card` component; `ews-glass`
is reserved for header/sidebar/window chrome only, per `ENTERPRISE_DESIGN_SYSTEM.md` §6.1's existing
chrome-vs-content rule, which this section applies specifically to the five files that currently
violate it.

## 3. Window behavior standard

Real, per `WINDOW_MANAGER.md` — this section states the standard other future window-like surfaces
should match, not a new design:

| Behavior | Standard |
|---|---|
| Open | `openApp(appId\|path)` → focus existing, restore minimized, or create cascaded — never a fourth outcome |
| Move/resize | Drag titlebar / SE handle; persist on pointer-up, not on every pixel of movement |
| Minimize/maximize/snap | Traffic-light controls; snap remembers the pre-snap restore rect |
| Close | Pushes onto a reopen stack (`Cmd/Ctrl+Shift+T`), never a hard delete of window state |
| Embed contract | Window body is `<iframe src="{path}?embed=1" loading="lazy" />` — **every** page a window can host must honor `?embed=1` by suppressing its own chrome; today only `WorkspaceLayout` and `SettingsPage` do (`TECH_DEBT.md` TD-44) — this is the standard every other Hub page should be brought up to, not a design choice unique to those two. |
| Animation | EDL classes only (`edm-overlay-panel`, dock scale transition) — no bespoke window-specific motion. |

## 4. Dock and Command Palette standard

- **Dock:** pinned + running + recent apps, hover-scale, badges, minimize/restore — real, per
  `DESKTOP.md`. Standard: any future "OS-level" summary surface (a future notification tray variant,
  say) should extend the Dock's existing badge/hover-scale conventions rather than inventing new ones.
- **Command Palette:** one live implementation (`UniversalCommandPalette`), four modes (palette/omnibox/
  commands/ai). **Standard, restated from `NAVIGATION_IMPROVEMENTS.md` NAV-01:** there must be exactly
  one live Command Palette; the orphaned second implementation (`navigation/components/
  CommandPalette.tsx`) should be retired, not maintained as a parallel option, per this standard's own
  "one canonical component" principle.
- **Quick Actions ("Create X"):** standard requires every `create_*` action to open a real creation
  flow — the current behavior (logging an activity entry and showing a badge, `docs/USER_EXPERIENCE_
  BACKLOG.md` UXB-01) does not meet this standard and should be treated as non-compliant, not as an
  acceptable interim state.

## 5. Dialog standards

Real primitives: `Dialog`, `Modal`, `Drawer` (`src/web/src/ui/`, `ENTERPRISE_DESIGN_SYSTEM.md` §13's
catalog). Standard, confirmed by the audit to already be followed everywhere checked (a genuine
compliance success, not a gap): **no feature area may define its own modal/dialog-like component** —
Desktop, City, and Production Center all correctly avoid this today; this standard exists to keep it
true as new surfaces are added, especially inside Production Center's still-growing studio set.

- Dialog = task-focused, blocking, centered.
- Modal = the general elevated-card overlay (`ENTERPRISE_DESIGN_SYSTEM.md` §13).
- Drawer = side-anchored, non-blocking-adjacent content.
- A new "confirm this destructive action" need always uses `Dialog`, never a custom implementation.

## 6. Form standards

Real primitives: `Input`, `Select`, `Checkbox`, `Radio`, `Switch`, `Textarea`, `FormField`
(label + control + helper/error, `ENTERPRISE_DESIGN_SYSTEM.md` §13). Standard:

1. Every form control is wrapped in `FormField`, never a bare `Input` with an adjacent hand-styled
   label — this is what gives every form in the platform the same label/helper/error rhythm.
2. Validation errors set `invalid` on the control (→ danger border + `aria-invalid`), never a
   separately-styled error message with no control-level association.
3. **The Production Center's real create/generate forms (once ADB-22 lands) must use these primitives**
   — this standard is stated now, ahead of that work, specifically so the first real generation UI
   doesn't reach for a bespoke form pattern the way the Strip components reached for bespoke card
   markup.

## 7. Table standards

Real primitives: `Table`, `DataGrid`, `Pagination` (`ENTERPRISE_DESIGN_SYSTEM.md` §13). Standard,
directly responding to `DESIGN_SYSTEM_GOVERNANCE.md` §2.3's finding:

1. Any list of more than a handful of homogeneous records (agent rosters, job queues, asset libraries,
   notification lists beyond the toast/panel pair) uses `Table`/`DataGrid`, not a hand-rolled `<li>`/
   `<div>` list.
2. **This standard is currently not met** by Desktop, City, and Production Center's top-level pages,
   which render list-like content as plain rows (`DESIGN_SYSTEM_GOVERNANCE.md` §2.3) — flagged here as
   the concrete remediation target, not a hypothetical future risk.
3. The Enterprise City's still-vision accessible List View (`ARCHITECTURE_DECISIONS_BACKLOG.md` ADB-29)
   is the highest-value place to apply this standard first, since it is explicitly designed to be a
   real `DataGrid`-based surface already.

## 8. Dashboard standards

Real precedent: the Live Dashboard (`DASHBOARD.md`) — a CSS grid of `LiveWidgetChrome`-wrapped tiles,
each supporting collapse/refresh/fullscreen/pin/resize/drag-reorder, one shared event bus
(`dashboardEventBus`), one persistence key. Standard for any future dashboard-shaped surface (a
Production Center analytics view, a future Marketing Manager profile per
`docs/USER_EXPERIENCE_BACKLOG.md` UXB — see `ARCHITECTURE_DECISIONS_BACKLOG.md` ADB-35):

1. Reuse `LiveWidgetChrome` for the widget shell — collapse/refresh/fullscreen/pin/resize/drag-reorder
   should be identical everywhere a dashboard exists, never reinvented per surface.
2. Reuse the profile concept (a named, role-scoped default widget set,
   `DASHBOARD.md`'s CEO/Manager/Sales/Developer/Finance/Administrator list) rather than a bespoke
   per-surface configuration mechanism.
3. **`EnterpriseMetricsStrip`'s KPI-grid pattern (§2.1) is a legitimate second dashboard-adjacent
   pattern**, distinct from the full Live Dashboard — appropriate for a compact, non-interactive KPI
   summary embedded in a larger page (e.g., inside Command Center), not for a page whose primary purpose
   *is* the dashboard.

## Related documents

`DESIGN_SYSTEM_GOVERNANCE.md` (the charter this standard implements), `UI_NAMING_CONVENTIONS.md` (naming
for every pattern defined here), `DESIGN_TOKEN_STANDARD.md` (the token rules every pattern here
consumes), `ENTERPRISE_DESIGN_SYSTEM.md` §13 (the full component catalog), `WINDOW_MANAGER.md`,
`DESKTOP.md`, `DASHBOARD.md`, `COMMAND_CENTER.md` (the real implementations §3–§8 standardize against),
`ARCHITECTURE_DECISIONS_BACKLOG.md` ADB-29, ADB-35 (where §7/§8's remediation targets are scheduled),
`docs/USER_EXPERIENCE_BACKLOG.md` UXB-01, UXB-04 (the quick-action and embed-chrome gaps §4/§3 restate
as governance non-compliance).
