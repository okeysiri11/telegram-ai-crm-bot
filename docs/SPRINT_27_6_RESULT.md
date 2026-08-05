# Sprint 27.6 — Enterprise Live Dashboard

**Phase:** 3 — Interactive Enterprise Platform  
**App:** `src/web` · sprint `27.6`  
**Constraint:** Extend existing dashboard / shell — no UI redesign, no rewrite of prior sprints.

## Goal

Turn the dashboard into a **live Enterprise Operating System** with auto-updating runtime tiles, reusable widgets, layout engine, role profiles, event bus, and persistence.

## Implemented

1. **Runtime Dashboard** — CPU, Memory, AI Runtime, Providers, MCP, Agents, Jobs, Event Queue, Notifications, Sessions (auto-update)  
2. **Enterprise Widgets** — Health, AI Status, Activity, Notifications, Tasks, Projects, CRM, Finance, Knowledge, Calendar — with collapse / refresh / fullscreen / pin  
3. **Workspace Layout Engine** — drag reorder, resize colSpan, save / restore multiple layouts  
4. **Dashboard Profiles** — CEO · Manager · Sales · Developer · Finance · Administrator  
5. **Runtime Event Bus** — reacts to notifications, jobs, agents, runtime status, errors, background tasks  
6. **Persistence** — `ews_live_dashboard_v1` (positions, layout, profile, collapsed, filters, pinned)

## Architecture decisions

1. New orchestration package `src/live-dashboard/` (same pattern as `command-center-runtime/`).  
2. Single `LiveDashboardDataProvider` shares metrics/health — avoids N× poller render loops.  
3. Bridge existing `liveUpdates` + `notificationStore` instead of a second event system.  
4. Keep Morning Brief / Command Center / Platform Pulse sections — Live Dashboard is added above modules.  
5. CPU is a local smoothed estimate (no browser process CPU API); Memory uses `performance.memory` when present.

## Files

### Added — `src/web/src/live-dashboard/`

- `types.ts`, `liveDashboardCatalog.ts`, `liveDashboardStore.ts`  
- `dashboardEventBus.ts`, `useLiveRuntimeMetrics.ts`  
- `LiveDashboardDataContext.tsx`, `LiveWidgetChrome.tsx`  
- `LiveDashboardWidgets.tsx`, `LiveDashboardShell.tsx`, `liveDashboard.css`  
- `index.ts`, `liveDashboard.test.ts`

### Extended

| File | Change |
|------|--------|
| `pages/DashboardPage.tsx` | Mount `<LiveDashboardShell />` |
| `config/webConfig.ts` | sprint `27.6` |
| `test/foundation.test.ts` | sprint assertion |
| `docs/DASHBOARD.md` | Architecture guide |
| `docs/SPRINT_27_6_RESULT.md` | This report |

## Tests

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **92 passed** |
| build | OK |

## Screenshots

Capture after `npm run dev` → `/dashboard`:

1. Live Dashboard toolbar (profile + layout + CPU/Mem strip)  
2. Developer profile runtime tiles  
3. Widget chrome (pin / fullscreen / collapse)  
4. Drag reorder between widgets  
5. Saved custom layout in layout selector  

## Remaining work

- Host-level CPU/RAM from Observability API  
- Freeform absolute positioning (x/y)  
- Cross-device layout sync  
- Deduplicate RuntimeHealthWidget when enterprise_health is shown alongside shell StatusBar poller

## Verify

```bash
cd src/web && npm install && npm run lint && npm test && npm run build && npm run dev
```

Open `/dashboard` · switch Profile to **Developer** · drag widgets · Save layout.
