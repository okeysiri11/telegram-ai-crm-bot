# Sprint CQ-30.7 — Navigation & Information Architecture Review

**Scope:** navigation hierarchy, menus, sidebar, dashboard, search, global search, quick actions,
command palette, breadcrumbs — evaluated against the real, current `enterpriseRuNav.ts` (Sprint
30.2/30.7). Documentation only, `src` not modified.

## 1. Navigation hierarchy — one level deep, by design

The real sidebar is flat: 23 items, no nested sub-menus, each a single click from anywhere in the app
(assuming the sidebar itself is always visible, which `docs/UI_NAVIGATION.md`'s real Surfaces table
confirms). This is a genuine strength for a first-time user — no hidden hierarchy to learn.

- **Why it works:** every module the brief asks about (CRM, ERP, Знания/Knowledge, Продакшн/Production
  Studio, Маркетплейс/Marketplace, Аналитика/Analytics, Настройки/Settings) is one click from any
  screen, not buried in a sub-menu.
- **Impact:** positive — click-depth is not the risk in this navigation; label accuracy is (see
  `docs/UX_AUDIT.md`'s headline finding).
- **Priority:** N/A (confirmed working as intended).
- **Complexity:** N/A.
- **Evidence:** `enterpriseRuNav.ts:15-37`, `docs/UI_NAVIGATION.md`'s Surfaces table.

## 2. Sidebar — 23 real items, one mislabeled, one near-duplicate

Restated with precision from `docs/UX_AUDIT.md`: 23 real entries, of which 22 route to distinct real
destinations and one (`marketing`) is a mislabeled duplicate of `marketplace`. Category grouping
(`CATEGORY_LABEL_RU`: Основное/Бизнес/AI и продакшн/Операции/Платформа/Система) exists as a real
6-category taxonomy but was not confirmed to be visually applied to the flat sidebar list in this pass
— worth a direct UI check.

## 3. Dashboard — landing surface confirmed real

`{ id: "home", label: "Главная", route: "/dashboard" }` is the real default landing route, distinct
from `{ id: "workspace", label: "Рабочий стол", route: "/desktop" }`. Two real, differently-named
landing-adjacent concepts ("Главная"/Home vs. "Рабочий стол"/Desktop) — not a duplicate-screen problem
(both are confirmed distinct real routes), but worth a one-line clarification in onboarding copy about
which is "your starting point" vs. "your workspace," since the names alone don't make the distinction
obvious to a first-time user.

- **Priority:** P3.
- **Complexity:** S (copy only).

## 4. Search / Global Search

Real `SEARCH_CATEGORY_RU` covers 20 categories (clients, crm, projects, documents, ai_agents,
knowledge, tasks, commands, modules, dashboards, organizations, users, finance, erp, workflows,
marketplace, applications, reports, hr, widgets). **Inherits the headline Маркетинг/Маркетплейс bug**
directly: `marketplace: "Маркетинг"` means a search result for the Marketplace module displays under
a "Маркетинг" category header, compounding the sidebar/breadcrumb inconsistency into search results
too — the same root cause, third surface affected.

- **Priority:** P0 (same fix as `docs/UX_AUDIT.md`'s headline finding — one dictionary value, three
  affected surfaces).
- **Complexity:** S.
- **Evidence:** `enterpriseRuNav.ts`'s `SEARCH_CATEGORY_RU` constant.

## 5. Quick Actions

Real `RU_QUICK_ACTIONS`: 10 actions (open module, open client, open project, open AI agent, create
client, create project, create document, open map, create task, command palette). Well-scoped,
verb-first naming ("Открыть.../Создать..."), consistent Russian grammar throughout — no finding here,
cited as a positive example of consistent terminology to match elsewhere.

## 6. Command Palette

Real `qa_palette` quick action routes to `/command-center` with keywords `["палитра", "команда",
"ctrl"]` — confirms the real live palette (not the orphaned copy `docs/TECH_DEBT.md` TD-40 tracks) is
the one wired into the Russian quick-actions catalog. Worth explicit confirmation this stays true as
Sprint 30.7 lands, since TD-40's orphaned copy is exactly the kind of thing a UX pass could
accidentally resurrect.

## 7. Breadcrumbs

Real `BREADCRUMB_LABEL_RU` covers 40 real path segments — a substantial, mostly-consistent real
dictionary. Beyond the headline `marketplace` bug, two smaller observations:

- `"mission-control": "Мониторинг"` (Monitoring) and the sidebar's own `{ id: "monitoring", label:
  "Мониторинг", route: "/health" }` use the same Russian word for two different real routes
  (`/health` vs. a `mission-control` path segment) — not necessarily wrong (both may legitimately be
  "monitoring" in the user's mental model), but worth confirming they're not two competing monitoring
  surfaces (which would echo `docs/TECH_DEBT.md`'s TD-02 Mission Control naming pattern at a smaller
  scale).
- `"kernel": "Архитектура"` (Architecture) — the breadcrumb dictionary relabels the real `/kernel`
  route (which, per `docs/RUNTIME_CONSISTENCY.md`, CQ-30, is the real frontend Kernel/bootstrap
  runtime) as "Architecture" for the user-facing breadcrumb. This is a deliberate, reasonable UX choice
  (a user doesn't need to know "Kernel" as internal architecture vocabulary) but is worth flagging as
  the one place internal and user-facing naming deliberately diverge — should stay intentional, not
  accidental.

- **Priority:** P3 (verify intentionality of both).
- **Complexity:** S (confirm, no change likely needed).

## Non-goals

- No sidebar restructuring — the flat, one-click hierarchy is confirmed working well.
- No new search/command infrastructure — every finding here is a labeling fix within the real, existing
  system.

## Related documents

`src/web/src/navigation/enterpriseRuNav.ts` (real), `docs/UX_AUDIT.md` (CQ-30.7 sibling, the headline
finding this document's §2/§4 restate with surface-specific detail), `docs/TECH_DEBT.md` (TD-02,
TD-40), `docs/RUNTIME_CONSISTENCY.md` (CQ-30, real Kernel runtime).
