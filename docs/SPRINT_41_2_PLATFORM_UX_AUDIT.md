# Sprint 41.2 — Platform UX Audit & Polish

**MODE:** UX + ACCEPTANCE  
**BASELINE:** after Sprint 41.1 (GlobeFly Client journey)  
**Date:** 2026-08-06  
**Status:** COMPLETE  

No new enterprise functionality. Usability-only changes.

---

## Executive summary

| Score | Value | Notes |
|-------|------:|-------|
| **Overall UX** | **78 / 100** | Clear Client path; Owner/Pro still dense |
| **Production readiness** | **82 / 100** | Auth + CRM + shell usable |
| **Enterprise readiness** | **74 / 100** | Strips/builders remain complex for admins |
| **Client readiness** | **86 / 100** | View Mode Client + help + compact header |
| **Recommendation** | **READY** (guided pilot) | Not unsupervised full-platform go-live |

---

## What shipped in 41.2

1. **Page orientation bar** on every FullLayout page — Where / What / Actions / Result + ⓘ help  
2. **Expanded help catalog** (14+ modules) with purpose, when, result, time, difficulty, related modules  
3. **Compact header** — Logo · Search · Company · Notifications · ⚙ · Profile  
4. **Interface Settings** (`/settings?tab=interface`) — density, font 80–120%, menu width, view mode, theme, language, right-panel pin/auto-hide, a11y  
5. **Right panel** — collapsed by default; ESC / outside click closes when unpinned; pin mode  
6. **Nav dedupe** — removed duplicate Clients / Finance / Legal / Manufacturing entries from Business group  
7. **RU localization** — settings chrome, dock pin labels, interface keys  
8. Preferences persisted (`ewp_ui_preferences_v1`) and applied on boot  

---

## Screen review framework

Every major screen answered:

| Question | Mechanism |
|----------|-----------|
| Where am I? | Breadcrumbs + `page.where` orientation |
| What is this page? | Help purpose / `page.what` |
| What can I do? | Help workflow / `page.actions` |
| Expected result? | Help expectedResult / `page.result` |

---

## Top 50 problems (prioritized)

### Critical (fixed or mitigated in 41.2)

| # | Problem | Status |
|---|---------|--------|
| 1 | Header overloaded with advanced controls | Fixed — compact header |
| 2 | User lost without page purpose | Fixed — orientation bar |
| 3 | Help missing on most modules | Fixed — catalog + icon |
| 4 | Right panel always open / noisy | Fixed — collapsed + ESC/outside |
| 5 | View Mode buried / confused with security | Mitigated — Interface Settings + hint |
| 6 | Duplicate CRM nav entries | Fixed — deduped Business group |
| 7 | English Settings cards | Fixed — RU i18n |
| 8 | Font/density not adjustable | Fixed — Interface Settings |
| 9 | AI entry previously opened Builder | Fixed in 41.1 |
| 10 | Client saw platform strips | Fixed in 41.1 |

### High (remaining)

| # | Problem | Area |
|---|---------|------|
| 11 | Activity seed titles still English | Localization |
| 12 | Some CRM internal labels English | Localization |
| 13 | Documents upload UX uneven | Documents |
| 14 | Analytics hub shallow for GlobeFly | Reports |
| 15 | Orientation bar adds vertical space on small screens | Layout |
| 16 | Tooltip help is long (multi-line via title) | Help UX |
| 17 | Onboarding still can interrupt Client path | Onboarding |
| 18 | Quick Create may expose Pro actions in Client | Nav |
| 19 | Breadcrumbs sometimes technical path segments | Nav |
| 20 | Desktop / City still reachable via search | Search |

### Medium

| # | Problem |
|---|--------|
| 21 | Builder framework still English in body copy |
| 22 | Workspace tab overflow on many tabs |
| 23 | Notification badge always visible even at 0 |
| 24 | Company selector vs tenant login mismatch risk |
| 25 | Interface ⚙ uses glyph not text (a11y) |
| 26 | Density CSS not applied to all legacy EDS pages |
| 27 | High-contrast mode class only toggled, not fully themed |
| 28 | Module context nav can duplicate sidebar |
| 29 | Help related modules are ids not deep links |
| 30 | Status bar / runtime bar still English metrics in Owner mode |
| 31 | First-entry wizard language mix |
| 32 | Search results include hidden View Mode routes |
| 33 | Profile vs Settings overlap |
| 34 | Calendar empty-state weak |
| 35 | Tasks page lacks orientation-specific CTAs |
| 36 | Marketplace admin vs browse unclear |
| 37 | ERP learning curve high |
| 38 | Knowledge search English placeholders |
| 39 | Toast strip can stack with orientation bar |
| 40 | Mobile sidebar close label OK; header still wraps |

### Low

| # | Problem |
|---|--------|
| 41 | Logo “AE” not brand-explained |
| 42 | Version/sprint in Settings confuses clients |
| 43 | Pin/Auto labels short |
| 44 | Comfortable density underused default |
| 45 | uk locale incomplete vs ru |
| 46 | Demo seed invoices not shown on dashboard |
| 47 | Help difficulty only Russian words |
| 48 | No keyboard shortcut sheet in Client mode |
| 49 | Breadcrumb “›” vs `/` inconsistency with docs |
| 50 | Audit scores not live-instrumented |

---

## Top improvements delivered

1. Compact header reduces cognitive load (~40% fewer chrome controls)  
2. Interface Settings centralizes advanced UX  
3. Orientation + help answers the four customer questions  
4. Right panel dismiss patterns match modern SaaS  
5. Font/density/menu width for accessibility  
6. Cleaner Business navigation  
7. Preferences persist across sessions  

---

## Screens requiring redesign (later)

| Screen | Why |
|--------|-----|
| `/analytics` | Needs GlobeFly funnel / filters as first-class UI |
| `/documents` | Upload/preview/download flow must feel turnkey |
| `/platform-builder/*` | Still developer-oriented (OK if Owner/Developer only) |
| Activity seed / timeline | Replace English stubs with live RU events |
| Search | Filter by View Mode allowlist |

---

## Quick wins (next 1–2 sprints)

- Localize Activity seed + CRM leftover English  
- Filter command palette / search by View Mode  
- Replace ⚙ with labeled “Интерфейс” on md+  
- Deep-link help `related` modules  
- Hide Quick Create Pro actions in Client mode  

---

## Long-term improvements

- Full design-system density tokens across all modules  
- Dedicated GlobeFly analytics board  
- Document binary pipeline E2E  
- Live UX telemetry (clicks / time / rage clicks)  
- Complete uk parity  

---

## UX audit metrics (representative Client path)

| Page | Nav complexity | Visual overload | Info density | Learn time | Confidence | A11y |
|------|---------------:|----------------:|-------------:|-----------:|-----------:|-----:|
| Login | 2 | Low | Low | 2 min | High | Med |
| Dashboard | 2 | Med | Med | 5 min | High | Med |
| CRM | 3 | Med | High | 20 min | Med | Med |
| Documents | 3 | Med | Med | 10 min | Med | Med |
| AI | 2 | Low | Med | 5 min | High | Med |
| Analytics | 2 | Med | Med | 15 min | Med | Med |
| Settings/Interface | 2 | Low | Med | 5 min | High | High |
| Notifications panel | 1 | Low | Med | 2 min | High | Med |

---

## Localization status

| Surface | RU Client |
|---------|-----------|
| Header / breadcrumbs / orientation | PASS |
| Interface Settings | PASS |
| Dock pin/collapse | PASS |
| Nav Business group | PASS |
| Activity seed titles | PARTIAL |
| CRM/Documents internals | PARTIAL |
| Builder body (hidden in Client) | N/A for Client |

---

## Quality gates

| Gate | Status |
|------|--------|
| Frontend tests (41.2 prefs + prior 41.1) | PASS |
| Lint / tsc | PASS (run in sprint) |
| No new backend APIs | PASS |
| Client View Mode preserved | PASS |

---

## Recommendation

**READY** for a **guided commercial pilot** (GlobeFly Client View Mode).  

**NOT READY** for unsupervised enterprise-wide rollout of Owner/Developer surfaces without further localization and analytics/documents depth.

---

## Files touched (primary)

- `src/web/src/preferences/preferencesStore.ts`  
- `src/web/src/preferences/InterfaceSettingsPanel.tsx`  
- `src/web/src/preferences/InterfacePreferencesBoot.tsx`  
- `src/web/src/preferences/preferences_41_2.test.ts`  
- `src/web/src/navigation/TopNavigation.tsx`  
- `src/web/src/shell/enterprise/ActivityPanel.tsx`, `DockPanel.tsx`  
- `src/web/src/help/moduleHelpCatalog.ts`, `PageOrientationBar.tsx`, `ModuleHelpIcon.tsx`  
- `src/web/src/pages/SettingsPage.tsx`  
- `src/web/src/layouts/FullLayout.tsx`, `shell/Providers.tsx`  
- `src/web/src/i18n/messages.ts`  
- `src/web/src/ux-revolution/intelligentNavGroups.ts`  
- `docs/SPRINT_41_2_PLATFORM_UX_AUDIT.md`
