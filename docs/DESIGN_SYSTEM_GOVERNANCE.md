# Design System Governance

**Status:** permanent governance charter. Documentation only — no source code was modified to produce
this document. This is the top-level authority for how UI components are built, named, and reused
across the platform — the "constitution" the other three governance documents
(`COMPONENT_LIBRARY_STANDARD.md`, `UI_NAMING_CONVENTIONS.md`, `DESIGN_TOKEN_STANDARD.md`) implement in
detail. It does not repeat `ENTERPRISE_DESIGN_SYSTEM.md`'s token values or `06_DESIGN_LANGUAGE.md`'s
visual principles — it governs *compliance* with them, based on a direct audit of real code across
Enterprise Desktop, Enterprise City, CRM, Production Center, AI Studio, Marketplace, Knowledge,
Dashboards, Forms, Tables, Dialogs, Notifications, Windows, Dock, and Command Palette.

## 1. The one governing principle

**One canonical component library (`src/web/src/ui/`), reused everywhere, extended rarely, duplicated
never.** This is not a new rule — it is `02_PRODUCT_PHILOSOPHY.md` principle 7 ("one pattern, many
adopters") applied specifically to UI components. This document exists because the audit behind it
found that principle genuinely honored in some places and genuinely violated in others, in ways worth
naming precisely rather than gesturing at.

## 2. What the audit found — stated plainly, since governance without evidence is just opinion

A direct read of `src/web/src/enterprise-desktop/`, `src/web/src/enterprise-city/`,
`src/web/src/ai-production-studio/`, `src/web/command-center/`, `src/web/src/command-center-runtime/`,
`src/web/src/shell/enterprise/`, and every `enterprise-*`/`*-strip` feature folder found:

### 2.1 Duplicated components

- **The "Strip" pattern — twelve near-identical components, no shared primitive.**
  `GovernanceStrip.tsx`, `MarketplaceStrip.tsx`, `OkrStrip.tsx`, `AIBuilderStudioStrip.tsx`,
  `ControlTowerStrip.tsx`, `DataFabricStrip.tsx`, `IntegrationHubStrip.tsx`, `EnterpriseTwinStrip.tsx`,
  `LearningStrip.tsx`, `AutonomyStrip.tsx`, `AIRuntimeStrip.tsx`, `PredictiveStrip.tsx` all render the
  identical shape (a labeled row + `Badge`(s) + a link, `docs/COMPONENT_LIBRARY_STANDARD.md` §2 has
  the full anatomy) — each hand-rolling its own container markup and its own bespoke CSS class
  (`gov-strip`, `mkt-strip`, `okr-strip`, `ect-strip`, `edf-strip`, `eih-strip`, `etwin-strip`,
  `sle-strip`, `auto-strip`, `art-strip`, `pred-strip`, `abs-strip` — twelve class names for one
  pattern) instead of importing one shared `Strip` component that doesn't exist yet.
- **Two parallel icon systems.** The canonical design-system icon library
  (`src/web/design-system/icons/index.tsx`) and a second, independent inline-SVG icon component
  (`src/web/src/shell/enterprise/ShellIcons.tsx`, its own comment reads "no new icon package
  dependency" — i.e., built specifically to avoid depending on the first one). `enterprise-desktop/`
  imports from the second, not the first.
- **`ews-glass` reused as an ad hoc card surface outside its intended chrome-only scope.** A CSS class
  owned by the shell (`enterpriseShell.css`, intended for header/sidebar chrome per
  `ENTERPRISE_DESIGN_SYSTEM.md` §6.1's chrome-vs-content rule) is applied directly to *content*
  surfaces in `DesktopShell.tsx`, `DesktopLauncher.tsx`, `StudioWorkspace.tsx`,
  `EnterpriseCityPage.tsx`, and `AIProductionCenterPage.tsx` — five feature files reaching for a chrome
  class to build what is, visually, a card, instead of the real `Card` component.
- **Inconsistent card usage within a single file.** `AIProductionCenterPage.tsx` uses the real `Card`
  component in some places and hand-styled `ews-glass`-wrapped `<li>`/`<header>` elements in others, for
  visually equivalent surfaces, in the same file.

### 2.2 Inconsistent naming

At least six distinct component-suffix conventions coexist with no stated rule for which to use when:
`*Page` (`EnterpriseCityPage`, `AIProductionCenterPage`), `*Shell` (`DesktopShell`), `*Frame`
(`WindowFrame`), `*Dock` (`EnterpriseDock`, `LeftDock`, `BottomDock`), `*Panel` (`DockPanel`,
`ActivityPanel`, `AiCommandCenterPanel`, `GlobalActivityFeedPanel`), `*Strip` (§2.1), `*Bar`
(`UniversalQuickActionsBar`, `StatusBar`), `*Widget` (`RuntimeHealthWidget`), `*Grid`
(`EnterpriseModuleGrid`), `*Workspace` (`StudioWorkspace`), and no suffix at all
(`Omnibox`, `CommandCenterProvider`). `DockPanel.tsx` combines two of these families in one name.
`ShellIcons.tsx` is plural but exports a singular `ShellIcon` function. Full remediation:
`UI_NAMING_CONVENTIONS.md`.

### 2.3 Inconsistent UX

- **No consistent internal folder shape** across feature areas — some use a Zustand-style store
  (`enterprise-desktop`, `ai-production-studio`), some use a pure derive function
  (`enterprise-governance`, `enterprise-okr`), some have a `Strip` summary component, some don't; only
  the `index.ts` barrel is consistently present everywhere.
- **List/table-like data is rendered as plain `<li>`/`<div>` rows** in Desktop, City, and Production
  Center's top-level pages rather than the real `Table`/`DataGrid` primitives — not a reimplementation
  of a table (none was found, which is a genuine positive finding, §2.4), but a missed opportunity to
  use one.
- **No feature area currently reimplements Dialog/Modal/Table** — confirmed by direct grep, zero
  matches. This is stated here as a real, positive finding: the platform has not (yet) drifted into the
  worse failure mode of parallel dialog/modal systems, only the lesser one of inconsistent card/icon/
  naming usage. Governance exists to keep it that way as more surfaces get built, not to fix an
  existing dialog-duplication problem that doesn't exist.

### 2.4 Reusable opportunities

1. **Extract a shared `Strip` primitive** into `src/web/src/ui/` — the single highest-value, lowest-
   risk fix available: twelve components collapse to one, with feature-specific content passed as
   props/children rather than each folder re-deriving the same container markup.
2. **Consolidate to one icon system.** `ShellIcons.tsx` should either be merged into
   `src/web/design-system/icons/index.tsx` (if its icons are genuinely needed and missing from the
   canonical set) or retired in favor of it.
3. **Extend the real `Card` component**, if it doesn't already support what `ews-glass` is being
   reached for (e.g., a lighter-weight card variant) — rather than leaving five files bypassing it.
4. **Route table-like content in Desktop/City/Production Center through the real `Table`/`DataGrid`**
   primitives now, before more list-as-`<li>` instances accumulate.

## 3. Governance process

1. **Before adding a new UI component**, check `COMPONENT_LIBRARY_STANDARD.md`'s pattern catalog — if
   an existing pattern fits (Card, Strip once built, Dialog, Table), extend it; a new component is only
   justified when none fits, per `UX_GUIDELINES.md`'s own "does this already exist" checklist item.
2. **Every new component's name** must follow `UI_NAMING_CONVENTIONS.md`'s fixed suffix vocabulary — a
   PR introducing a seventh unlisted suffix should be rejected on this rule alone, the same way
   `ENTERPRISE_DESIGN_SYSTEM.md` §2 already treats a hardcoded color value as a defect.
3. **Every new color/spacing/motion value** must come from `DESIGN_TOKEN_STANDARD.md`'s governed token
   set — a raw utility-class color (e.g., the Strip pattern's `text-[var(--eds-primary)]` written
   inline instead of through a component class) is flagged the same way.
4. **This document's §2 findings are the seed of a living audit**, not a one-time snapshot — the next
   full audit should re-check whether the Strip consolidation (§2.4 item 1) and icon consolidation
   (§2.4 item 2) have happened, and add any new duplication pattern found since.

## Related documents

`COMPONENT_LIBRARY_STANDARD.md`, `UI_NAMING_CONVENTIONS.md`, `DESIGN_TOKEN_STANDARD.md` (the three
documents this charter governs), `ENTERPRISE_DESIGN_SYSTEM.md`, `06_DESIGN_LANGUAGE.md`,
`07_DESIGN_SYSTEM.md` (the visual/token canon this governance enforces compliance with, not
duplicates), `UX_GUIDELINES.md` (the practical pre-ship checklist this charter's process section
extends), `docs/UX_REVIEW.md`, `docs/USER_EXPERIENCE_BACKLOG.md` (related but distinct — those audit
user-facing interaction friction; this audits component-implementation consistency),
`ARCHITECTURE_DECISIONS_BACKLOG.md` (where a governance finding here graduates into a scheduled fix).
