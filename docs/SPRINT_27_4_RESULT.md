# Sprint 27.4 — Enterprise Workspace Runtime

**Phase:** 3 — Interactive Workspace & Functional Modules  
**App:** `src/web` · sprint `27.4`  
**Constraint:** Extend existing shell / workspace-engine — no architecture redesign.

## Goal

Transform the platform from a collection of pages into a persistent **Enterprise Workspace Runtime**: live tabs, dockable panels, pro tab chrome, grouped search, universal create, notification center, and live Runtime Health.

## Implemented

### 1. Live Workspace

- Session snapshot **v2** (`ews_workspace_session_v1`): tabs, active tab, active workspace id, **closed-tab stack**
- Route sync keeps tabs aligned with navigation (`useWorkspaceRouteSync`)
- Last module + dock layout persistence (`ews_dock_layout_v1`) for panel window sizes / pin / auto-hide

### 2. Dockable Panels

- `shellLayoutStore` docks: **left · right · bottom**
- Each dock: **collapse · resize · pin · auto-hide** (`DockPanel`)
- Left dock: module shortcuts + recent activity (toggle from header)
- Right dock: Activity Center (notifications + journal)
- Bottom dock: Runtime Health (toggle **Health** in header)

### 3. Workspace Tabs (VS Code / JetBrains style)

- Drag **reorder**
- Close / pin / **duplicate**
- **Reopen closed** (↶ button + context menu)
- Right-click context menu

### 4. Global Search

- Index extended with create commands (task, document, agent, workflow, knowledge, company)
- `searchProvider.searchGrouped()` returns **grouped** hits
- `/search` UI shows Modules + **Grouped results** (CRM, ERP, AI Agents, Documents, Settings/modules, Users, Projects, Knowledge, Commands, …)

### 5. Quick Create

- Universal **+ Create** FAB (`QuickCreateButton`)
- Entities: Client · Project · Task · Document · AI Agent · Workflow · Knowledge Page · Company
- Aligned with `ENTERPRISE_QUICK_ACTIONS` + command palette `create_company`

### 6. Notification Center

- Buckets: **Unread · Mentions · Warnings · Errors · Success · Jobs**
- Kinds extended: `mention`, `job`
- Dashboard panel + Activity dock notifications tab

### 7. Runtime Health

- Shared `useRuntimeHealth` poller (Frontend · Runtime · API · AI · Providers · Memory · Voice · MCP · …)
- Widget on Dashboard + bottom dock; StatusBar consumes same probe mapping

## Architecture decisions

1. **Extend, don’t fork** — `workspace-engine` + `shell/enterprise` remain the single runtime surface.
2. **Dock layout separate from tab session** — `ews_dock_layout_v1` vs `ews_workspace_session_v1` so panel geometry doesn’t couple to tab list.
3. **One probe catalog** — `STATUS_PROBES` + `useRuntimeHealth`; no third health implementation.
4. **Grouped search on existing categories** — reuse `SearchCategory`; UI groups, index unchanged in shape.
5. **Create = navigate to hub action** — deep forms deferred; FAB/palette open module create routes.

## Files changed (primary)

| Area | Paths |
|------|--------|
| Workspace runtime | `src/workspace-engine/types.ts`, `workspaceManagerStore.ts`, `WorkspaceTabBar.tsx`, `QuickCreateButton.tsx`, `quickCreateCatalog.ts`, `NotificationCenterPanel.tsx`, `DashboardWorkspaceWidgets.tsx`, `QuickActionsPanel.tsx`, `index.ts`, `workspaceEngine.test.ts` |
| Shell / docks | `shell/enterprise/shellLayoutStore.ts`, `DockPanel.tsx`, `LeftDock.tsx`, `BottomDock.tsx`, `RuntimeHealthWidget.tsx`, `useRuntimeHealth.ts`, `ActivityPanel.tsx`, `StatusBar.tsx`, `enterpriseShell.css`, `index.ts` |
| Layout / nav | `layouts/FullLayout.tsx`, `navigation/TopNavigation.tsx` |
| Search | `navigation/managers/searchProvider.ts`, `searchIndex.ts`, `modules/SearchWorkspacePage.tsx` |
| Notifications | `notifications/notificationStore.ts` |
| Pulse / config | `modules/PlatformPulsePanel.tsx`, `config/webConfig.ts`, `test/foundation.test.ts` |
| Palette | `command-center/managers/quickActions.ts` |
| Docs | `docs/SPRINT_27_4_RESULT.md` |

## Tests

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **81 passed** |
| build | OK |
| render-loop smoke | OK (prior suite retained) |
| browser smoke | Dashboard + CRM + Create FAB; no Maximum update depth |

Coverage added: tab reorder/duplicate/reopen, dock persistence, grouped search, quick create catalog, notification buckets.

## Screenshots

Capture from local run (`npm run dev` → typically `http://localhost:5180` or next free port):

1. **Dashboard** — Runtime Health card + Notification Center buckets  
2. **Tab bar** — multi-module tabs + reopen / context menu  
3. **Docks** — Left dock open · Activity right dock resized · bottom Health dock  
4. **Quick Create** — FAB menu (Client → Company)  
5. **Search** — grouped results for query `create` or `crm`

*(Binary screenshots not committed in this sprint; verify visually in the running shell.)*

## Remaining work

- Keep-alive tab content (avoid remount on `key={loc.pathname}`)
- Shared singleton health poller (reduce parallel `useRuntimeHealth` intervals)
- Server-backed notifications / WebSocket jobs
- Deep create forms (not query-action hubs only)
- Drag-drop floating panels outside fixed L/R/B docks

## Verify

```bash
cd src/web && npm install && npm run lint && npm test && npm run build && npm run dev
```

Demo login (local): `owner@demo.corp` / `demo` · tenant `demo-corp`
