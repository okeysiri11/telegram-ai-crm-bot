# UI Naming Conventions

**Status:** permanent standard. Documentation only — no source code was modified to produce this
document. Fixes the six-plus coexisting suffix conventions found by the audit behind
`DESIGN_SYSTEM_GOVERNANCE.md` §2.2 with one fixed vocabulary, plus file, folder, and CSS-class naming
rules. Governed by `DESIGN_SYSTEM_GOVERNANCE.md`.

## 1. Component naming — the fixed suffix vocabulary

**Problem:** the audit found `*Page`, `*Shell`, `*Frame`, `*Dock`, `*Panel`, `*Strip`, `*Bar`,
`*Widget`, `*Grid`, `*Workspace`, and no-suffix components all coexisting with no rule for which to use
when — real examples: `EnterpriseCityPage`, `DesktopShell`, `WindowFrame`, `EnterpriseDock`,
`DockPanel`, `GovernanceStrip`, `StatusBar`, `RuntimeHealthWidget`, `EnterpriseModuleGrid`,
`StudioWorkspace`, `Omnibox`.

**Standard — one suffix per semantic role, not per feature area:**

| Suffix | Means | Real examples that already match |
|---|---|---|
| `*Page` | The routed entry component for a feature — exactly one per feature folder | `EnterpriseCityPage`, `AIProductionCenterPage` |
| `*Shell` | An outer OS-level chrome container hosting other components | `DesktopShell` |
| `*Frame` | A single movable/resizable window instance | `WindowFrame` |
| `*Dock` | A pinned/running-app tray | `EnterpriseDock`, `LeftDock`, `BottomDock` |
| `*Panel` | A docked or embedded chrome panel that is not itself a window or a dock | `ActivityPanel`, `AiCommandCenterPanel` |
| `*Strip` | The compact summary primitive (`COMPONENT_LIBRARY_STANDARD.md` §2.1) | `GovernanceStrip`, `OkrStrip`, etc. |
| `*Bar` | A persistent, thin, full-width chrome element | `StatusBar` |
| `*Widget` | A single-purpose Dashboard tile (used inside `LiveWidgetChrome`, `COMPONENT_LIBRARY_STANDARD.md` §8) | `RuntimeHealthWidget` |
| `*Catalog` | A static data/config module, not a component | `productionCatalog.ts`, `cityCatalog.ts` |
| `*Store` | A Zustand store module, not a component | `desktopStore.ts`, `productionStore.ts` |

**Deprecated/to-be-renamed on next touch (not renamed by this documentation-only pass):**

- `EnterpriseModuleGrid` — "Grid" is not in the fixed vocabulary; rename to whichever real role it
  plays (likely `*Panel` if it's a chrome container, or fold into a `*Page`).
- `StudioWorkspace` — "Workspace" collides with the platform-wide Workspace concept
  (`ENTERPRISE_DESIGN_SYSTEM.md` §15); rename to `StudioPage` or `StudioPanel` depending on whether it's
  routed directly or embedded.
- `DockPanel` — combines two vocabulary entries in one name; should be `DockFrame` or simply live inside
  `*Dock`'s own file without a separate `*Panel` name.
- `ShellIcons.tsx` — plural filename, singular export (`ShellIcon`); rename the file to match its export,
  and see §4 for the larger icon-system question this file is part of.
- `Omnibox`, `CommandCenterProvider` — acceptable as-is: `Omnibox` is a proper-noun UI concept (like
  "Dock" or "Palette") that doesn't need a generic suffix; `*Provider` is a legitimate tenth vocabulary
  entry for a React context provider specifically, added here since it's a real, distinct role none of
  the above ten covers.

## 2. File and folder naming

- **Feature folders:** kebab-case, matching the route/concept they represent
  (`enterprise-city`, `enterprise-desktop`, `ai-production-studio`) — already consistent across the
  audited folders, no change needed.
- **Component files:** PascalCase matching the exported component name exactly (`DesktopShell.tsx`
  exports `DesktopShell`) — already consistent, no change needed.
- **Non-component files:** camelCase (`cityEngine.ts`, `productionCatalog.ts`, `desktopStore.ts`) —
  already consistent, no change needed.
- **One file, one primary export.** Every audited file already follows this — stated here as the
  standard to preserve, not a gap to fix.

## 3. CSS class naming

**Problem:** the Strip pattern alone produced twelve unrelated class names (`gov-strip`, `mkt-strip`,
`okr-strip`, `ect-strip`, `edf-strip`, `eih-strip`, `etwin-strip`, `sle-strip`, `auto-strip`,
`art-strip`, `pred-strip`, `abs-strip`) for one visual pattern, each a different feature-specific
abbreviation prefix.

**Standard:** once `Strip` becomes a real shared component (`COMPONENT_LIBRARY_STANDARD.md` §2.1), it
needs exactly **one** class name (e.g., `.eds-strip`), with feature-specific styling (if any is
genuinely needed beyond props-driven content) applied via a data attribute or a single BEM-style
modifier (`.eds-strip--governance`), never a wholesale independent class per feature. This mirrors how
`ENTERPRISE_DESIGN_SYSTEM.md` §13's `.eds-card` already works (one base class, documented modifiers like
`.eds-card--raised`/`--interactive`) — the Strip components are the one place this convention wasn't
followed, and this section states the fix precisely.

**General rule going forward:** a new component's CSS class is named for the *component*, not the
*feature that happens to use it first* — `gov-strip` names the Governance feature, not the Strip
pattern, which is exactly backwards for a shared primitive.

## 4. Icon naming and the two-icon-system question

**Problem:** two icon systems exist — the canonical `src/web/design-system/icons/index.tsx` and a
second, independent `src/web/src/shell/enterprise/ShellIcons.tsx`, the latter built specifically to
avoid depending on the former (per its own code comment). `enterprise-desktop/` uses the second one
exclusively.

**Standard:**

1. **One icon system.** Every new icon need should first check `iconLibrary`
   (`design-system/icons/index.tsx`) before reaching for `ShellIcons.tsx` or a raw glyph.
2. **If `ShellIcons.tsx` exists because of a real technical constraint** (e.g., it needs to render
   before the design-system bundle loads, or avoids a genuine circular dependency), that reason should
   be written down as a comment in the file itself — today it states only that it avoids "a new icon
   package dependency," which does not explain why the *existing* one wasn't reused instead of building
   a second one.
3. **Until the two are merged or the separation is justified in writing, treat any new icon as
   belonging in the canonical `iconLibrary`** — this prevents the two-system problem from growing while
   the underlying question (`DESIGN_SYSTEM_GOVERNANCE.md` §2.4 item 2) is resolved.
4. **Raw Unicode glyphs used as icons** (found in `cityCatalog.ts`'s dingbat symbols, `WindowFrame.tsx`'s
   `⛶` maximize glyph, the `★` favorite/rating glyphs in `EnterpriseCityPage.tsx`/
   `AIProductionCenterPage.tsx`/`EnterpriseMarketplacePage.tsx`) are **not** literal emoji (confirmed by
   direct audit — a correction worth stating plainly, since emoji-as-chrome was the specific concern
   `ENTERPRISE_DESIGN_SYSTEM.md` §10 already flagged and swept once). They are, however, still outside
   the canonical icon system — a raw `⛶` maximize glyph should become a real `Icon` library entry the
   next time `WindowFrame.tsx` is touched, following the icon library's existing stroke-based SVG
   contract (`ENTERPRISE_DESIGN_SYSTEM.md` §10) rather than a Unicode character with no consistent
   sizing/color/theme behavior.

## 5. Naming collisions to resolve (cross-referenced, not re-described)

- **"Strip" used for two different things** — the compact-summary primitive (§ throughout this
  document) and `EnterpriseMetricsStrip`'s KPI-grid pattern (`COMPONENT_LIBRARY_STANDARD.md` §8 item 3)
  — recommend renaming the latter to `EnterpriseMetricsGrid` or similar on next touch, since it is a
  materially different component sharing a name by coincidence, the same class of problem as
  "Portal"/"Production"/"Enterprise AI OS" already tracked in `PRODUCT_ARCHITECTURE_REVIEW.md`.
- **"Workspace" collision** — `StudioWorkspace.tsx` vs. the platform-wide Workspace concept (§1's
  deprecation note).

## Related documents

`DESIGN_SYSTEM_GOVERNANCE.md` (the charter), `COMPONENT_LIBRARY_STANDARD.md` §2.1 (the Strip primitive
this document's class-naming section fixes), `ENTERPRISE_DESIGN_SYSTEM.md` §10 (the canonical icon
library this document defers to), `PRODUCT_ARCHITECTURE_REVIEW.md` (the "Portal"/"Production"/
"Enterprise AI OS" naming-collision pattern this document's §5 extends to component names).
