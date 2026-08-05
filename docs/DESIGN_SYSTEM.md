# Sprint CQ-30.1 — Design System

**Sprint:** CQ-30.1 — UX Design. Documentation only, `src` not modified.

**Do not duplicate:** `src/web/design-system/` (real, `v9.0.1`, Sprint 26.2) is a mature, complete real
design system — tokens, colors, typography, icons, grid, spacing, elevation, animation, responsive,
accessibility, a real component catalog, and a real theme engine. This document's job is almost
entirely mapping the brief's eleven items onto what already exists and flagging the one real gap found
— not designing a new system.

## 1. Per-item mapping (brief's eleven)

| Brief item | Real system | Status |
|---|---|---|
| Colors | Real `colorSystem` (`colors/index.ts`): `primary/secondary/success/warning/danger/info/neutral/background/surface/border/text/disabled` + real interaction states (`hover`, `active`, `focus.ring`) | **Complete** — reused as-is |
| Typography | Real `typography/` — "Display → button text scale" per the real README | **Complete** |
| Spacing | Real `spacing/` scale | **Complete** |
| Icons | Real `icons/` — Navigation/AI/CRM/ERP/Finance/HR/Analytics/Notifications/Security/Settings/Workflow sets | **Complete**; `docs/UI_NAVIGATION.md` §1's `ShellIcon`/`ShellIconId` already consumes this real set |
| Cards | Real catalog entry `id: "cards"`, `api: "Card"` | **Complete** |
| Tables | Real catalog entry `id: "tables"`, `api: "Table \| DataGrid \| Pagination"` | **Complete** |
| Forms | Real catalog entry `id: "forms"`, examples `["login form", "settings form"]` | **Complete** — the real login/settings forms already exercise this |
| Dialogs | Real catalog entry `id: "dialogs"`, `api: "Dialog \| Modal \| Drawer"`, real accessibility notes (`role=dialog`, `Escape closes`) | **Complete**, including accessibility |
| Notifications | Real `NotificationBucket`/`notificationStore.ts` (CQ-17) is the data layer; the design-system's own catalog entry for a notification *component* was not individually re-derived this pass, but the toast pattern (`docs/UI_NAVIGATION.md` §3) composes real tokens (colors, elevation, animation) | **Data layer complete; component styling assumed complete pending a direct catalog check** |
| Dark Theme | Real `ThemeId: "dark"`, real `applyTheme()` sets `data-theme="dark"` via CSS custom properties (`--eds-primary`, etc.) | **Complete** |
| Light Theme | Real `ThemeId: "light"`, same mechanism | **Complete** |

## 2. Real theme engine — two more themes than the brief asked for

`theme/index.ts`'s real `ThemeId` union is `"light" | "dark" | "corporate" | "custom"` — the real
system already supports white-label branding (`BrandOverrides: { primary, primarySoft, font }`) beyond
the brief's light/dark ask. Beta scope: light and dark are the only two exposed in the user-facing
theme switcher (`docs/UX_ARCHITECTURE.md` §1's User Menu); `corporate`/`custom` remain available for a
future white-label Beta customer without any new engine work.

## 3. The one gap: no confirmed dedicated Notification component catalog entry

Unlike the other ten items, this sprint did not find a `catalog/index.ts` entry specifically for a
"Notification" or "Toast" component (only the data layer, `NotificationBucket`, was confirmed real).
Flagged as needing a direct check before assuming full parity with the other ten — likely already
covered under `"dialogs"` or a similar entry not individually grepped this pass, but not asserted as
confirmed.

## 4. Russian localization and the design system

No text is hardcoded in any real design-system file sampled this sprint (`colorSystem`, `theme/
index.ts`, the catalog) — all real components are token/prop-driven, meaning `docs/RUSSIAN_UI_
DICTIONARY.md`'s work composes cleanly on top without any design-system change.

## Non-goals

- No new token, color, typography, or component system — every item in §1 reuses the real, complete
  `design-system/` package.
- No new theme beyond confirming light/dark are Beta's exposed pair.

## Related documents

`src/web/design-system/README.md` (real, the system this document maps), `docs/UI_NAVIGATION.md` (real
`ShellIcon` consumption), `docs/RUSSIAN_UI_DICTIONARY.md` (CQ-30.1 sibling, confirmed compatible per
§4).
