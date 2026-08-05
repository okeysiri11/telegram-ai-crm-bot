# Sprint 27.5 — Enterprise Command Center

**Phase:** 3 — Interactive Workspace & Functional Modules  
**App:** `src/web` · sprint `27.5`  
**Constraint:** Extend existing workspace + `command-center/` — no architecture redesign.

## Goal

Create the **Enterprise Command Center** — the central control hub for the platform: VS Code–style palette, live activity, AI ops panel, KPIs, universal actions, enhanced status bar, and keyboard-first navigation.

## Implemented

1. **Command Palette** — sections: Recent · Favorites · Open module · Create · AI · Developer; Ctrl/Cmd+K  
2. **Global Activity Feed** — merged timeline (AI, system, CRM, user, jobs, notifications, workflows, errors, warnings)  
3. **AI Command Center** — running / queued / completed · providers · memory · model · time · cost  
4. **Enterprise Metrics** — Projects, Clients, Tasks, Revenue, AI Agents, Workflows, Health, API  
5. **Universal Quick Actions** — create + open from dashboard and `/command-center`  
6. **Enterprise Status Bar** — Env · Workspace · User · Runtime · Git · Conn · AI · Alerts · Jobs  
7. **Keyboard navigation** — search, tabs, close/reopen, next/prev panel, home  
8. **Docs** — `docs/COMMAND_CENTER.md` + this result

## Architecture decisions

1. Thin **`command-center-runtime/`** orchestration layer; keep palette engines in `command-center/`.  
2. Palette sections built from `COMMAND_CATALOG` + `DEVELOPER_COMMANDS` + persisted recent/favorites.  
3. Activity feed merges journal + notifications (no second store).  
4. Status bar extends Sprint 27.4 `useRuntimeHealth` with `useEnterpriseStatus`.  
5. Keyboard: provider keeps palette hotkeys; `useEnterpriseKeyboard` in FullLayout handles workspace/tabs/panels.

## Files modified / added

### Added — `src/web/src/command-center-runtime/`

- `developerCommands.ts`, `commandFavorites.ts`, `paletteSections.ts`  
- `globalActivityFeed.ts`, `GlobalActivityFeed.tsx`  
- `AiCommandCenterPanel.tsx`, `EnterpriseMetricsStrip.tsx`  
- `UniversalQuickActionsBar.tsx`  
- `useEnterpriseStatus.ts`, `useEnterpriseKeyboard.tsx`  
- `index.ts`, `commandCenterRuntime.test.ts`

### Extended

| Area | Files |
|------|--------|
| Palette | `command-center/components/UniversalCommandPalette.tsx`, `managers/security.ts`, `types.ts`, `pages/CommandCenterPage.tsx` |
| Shell | `shell/enterprise/StatusBar.tsx`, `enterpriseShell.css`, `layouts/FullLayout.tsx` |
| Dashboard | `pages/DashboardPage.tsx` |
| Shortcuts | `navigation/managers/shortcutManager.ts` |
| Config / tests | `config/webConfig.ts`, `test/foundation.test.ts` |
| Docs | `docs/COMMAND_CENTER.md`, `docs/SPRINT_27_5_RESULT.md` |

## Keyboard shortcuts

See [COMMAND_CENTER.md](./COMMAND_CENTER.md#keyboard-shortcuts).

## Tests

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **87 passed** |
| build | OK |

## Screenshots

Capture locally after `npm run dev`:

1. Palette open (⌘K) with section headers  
2. Dashboard — Metrics + AI Command Center + Global Activity Feed  
3. Status bar — Env / User / Git / Conn / Jobs  
4. `/command-center` hub page  
5. Universal Quick Actions row  

*(Binary assets not committed; verify in the running shell.)*

## Remaining work

- Persist command analytics server-side  
- Real cost / token metering from providers  
- Unify live-ops `ActivityFeedPanel` into the global feed when MC is online  
- Shortcut customization UI  
- Voice / natural-language command mode

## Verify

```bash
cd src/web && npm install && npm run lint && npm test && npm run build && npm run dev
```

Open: Dashboard · press ⌘/Ctrl+K · `/command-center`  
Demo login: `owner@demo.corp` / `demo`
