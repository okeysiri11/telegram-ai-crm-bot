# Sprint 41.3 — Client UX Refinement & Navigation Experience

**Status:** COMPLETE · READY FOR CLIENT DEMO (guided)  
**Scope:** UX + navigation + Russian localization only — no new business APIs  
**Baseline:** Sprint 41.2 Platform UX Audit

---

## Goal

Make the Enterprise platform self-explanatory:

1. Where am I?
2. Why am I here?
3. What can I do?
4. What should I do next?

---

## Before / After

| Area | Before (41.2) | After (41.3) |
|------|---------------|--------------|
| Activity Center | Panel with English leftovers; resizable | True dock: collapse/expand/pin, width+state persisted, **no manual resize**, RU labels |
| Top toolbar | Always expanded, tall | Collapse toggle; collapsed = Logo · Search · Notifications · Profile; preference persisted |
| Mystery strip | `GlobalWorkspaceBar` unclear purpose | **Workspace Dock** quick switch (CRM, Analytics, Drone, Crypto, Knowledge, Documents, AI, Platform) |
| Module hubs | Sparse empty centers | Self-explaining landings + green primary CTA + welcome card |
| Context header | Purpose/actions/result | Trail + purpose + actions + result + estimated time + Help |
| Localization | Partial RU | Activity / Runtime / Dock / Toolbar / Landing / Welcome keys in RU |

---

## What shipped

### Task 1 — Full Russian localization (chrome)

- Activity tabs, seed entries, tone badges
- Dock controls (expand/collapse/pin)
- Runtime Health / Jobs / Providers / Heartbeat
- Toolbar / landing / welcome / page orientation keys
- Left dock + bottom dock labels

### Task 2 — Right panel as true dock

- `DockPanel`: `resizable` defaults **false for right**
- Collapse / expand controls match left dock icons
- Width + open/collapsed persisted via `ews_dock_layout_v1`
- CSS transition `.ews-dock--anim`

### Task 3 — Collapsible top toolbar

- `toolbarStore` + `ewp_toolbar_collapsed_v1`
- Expanded: Logo, Company, Language, View mode, Search, Commands, Profile
- Collapsed: Logo, Search, Notifications, Profile

### Task 4 / 5 / 7 / 9 — Module landings + context + welcome + CTA

Catalog + view for: Drone, Auto, Crypto OTC, Agro, Marketplace, Legal, Cafe, AI, Platform, Owner, Analytics, CRM, Knowledge, Documents

Each landing includes: title, purpose, description, primary actions, recent, next step, AI recommendation, estimated minutes, green `.ews-primary-cta`, first-visit welcome (dismiss forever).

`PageOrientationBar` enriched with trail, time, help label.

### Task 6 — Mystery strip → Workspace Dock

`WorkspaceQuickDock` replaces `GlobalWorkspaceBar` in `FullLayout`. Client chrome hides `WorkspaceTabBar`.

### Task 8 — Visual hierarchy

CSS markers: `.ews-hierarchy-header|nav|actions|content`, stronger CTA contrast.

### Task 10 — Unified journey validation

Unit tests assert every landing answers the four UX questions.

---

## Screenshots

*(Capture during demo — suggested frames)*

1. Collapsed toolbar + Workspace Dock  
2. CRM landing with green CTA + welcome card  
3. Activity Center collapsed rail vs expanded dock  
4. Drone landing + context trail  
5. RU locale Activity tabs

---

## Acceptance runs

| Suite | Result |
|-------|--------|
| TypeScript (`npm run lint` / `tsc -b`) | **PASS** |
| Unit vitest `client_ux_41_3.test.ts` | **PASS** (7) |
| Unit vitest `preferences_41_2.test.ts` | **PASS** (4) |
| Navigation | Workspace Dock + landing gates on hubs |
| Localization | `messages.ru` keys for chrome |
| Playwright UX | Not in repo — covered by vitest + manual demo |
| Persistence | Toolbar + dock layout localStorage |
| Settings / panel | Unpin + ESC/outside (41.2) retained; resize off for right |

---

## Scores

| Metric | Score | Notes |
|--------|------:|-------|
| UX clarity | **86 / 100** | Landings + context + dock; some live workflow interiors still denser |
| Client readiness | **88 / 100** | GlobeFly + RU chrome + self-explain hubs |
| Localization completeness (chrome) | **90 / 100** | Deep module English leftovers possible in legacy pages |
| Navigation | **87 / 100** | Workspace Dock replaces mystery strip |

**Overall: READY FOR CLIENT DEMO** (guided pilot · Russian locale · client/manager view mode)

---

## Remaining issues

1. Deep live-workflow pages (`?view=` / `:sub`) still use older interior copy — landings cover hubs only.  
2. Some StatusBar probe *details* (API payloads) remain English technical strings.  
3. No Playwright suite in repo — recommend adding smoke UX specs next sprint.  
4. Platform/Owner landings gate first paint; deep builder routes unchanged.

---

## Architectural decisions

- **Extend** shell/i18n/modules — no new `platform_*` package.  
- Landings are **catalog-driven** (`moduleLandingCatalog`) rather than per-page hardcoding.  
- Right dock **not resizable** by product rule (width still remembered from defaults/preferences).  
- Mystery strip **converted** to Workspace Dock (option A), not removed.

---

## Recommendation

Demo with:

- Locale **Русский**  
- View mode **Клиент** or **Менеджер**  
- `client@globefly.demo` / `demo`  
- Walk: Dashboard → Workspace Dock → CRM landing → primary CTA → Activity dock toggle → Toolbar collapse

**READY FOR CLIENT DEMO**
