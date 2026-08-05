# Enterprise Command Center

**Sprint:** 27.5  
**App:** `src/web`  
**Role:** Central control hub for the ADOS Enterprise Workspace.

## Architecture

```
CommandCenterProvider (palette / omnibox / AI hotkeys)
        │
        ├── UniversalCommandPalette  ← VS Code sections (Recent, Favorites, …)
        ├── command-center/managers  ← catalog, omnibox, AI, analytics, RBAC
        └── command-center-runtime/  ← feed, metrics, AI panel, keyboard, status
                │
FullLayout ── StatusBar · docks · tabs · useEnterpriseKeyboard
Dashboard ── Metrics · Quick Actions · AI Panel · Global Activity Feed
/command-center ── Productivity Hub page
```

**Extend, don’t replace:** the existing `command-center/` package remains the palette engine.  
`src/command-center-runtime/` orchestrates enterprise surfaces on top of workspace-engine + shell.

## Components

| Component | Path | Purpose |
|-----------|------|---------|
| `UniversalCommandPalette` | `command-center/components/` | ⌘/Ctrl+K palette with sections |
| `CommandCenterProvider` | `command-center/components/` | Hotkeys + overlay mount |
| `GlobalActivityFeed` | `command-center-runtime/` | Live timeline |
| `AiCommandCenterPanel` | `command-center-runtime/` | Agents / jobs / providers / cost |
| `EnterpriseMetricsStrip` | `command-center-runtime/` | KPI widgets |
| `UniversalQuickActionsBar` | `command-center-runtime/` | Create / open from anywhere |
| `StatusBar` | `shell/enterprise/` | Persistent enterprise footer |
| `useEnterpriseKeyboard` | `command-center-runtime/` | Tab / panel / search shortcuts |
| `CommandCenterPage` | `command-center/pages/` | `/command-center` hub |

## Command Palette

**Open:** `Ctrl+K` / `Cmd+K` (also Ctrl+Space)

**Modes (Tab):** palette · omnibox · commands · ai

**Empty palette sections:**

1. Recent  
2. Favorites (⌘/Ctrl+B toggles favorite on selected row)  
3. Open module  
4. Create  
5. AI commands  
6. Developer  

**Also:** Ctrl+P omnibox · Ctrl+Shift+P AI · Ctrl+/ commands

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl/Cmd+K | Open Command Palette |
| Ctrl/Cmd+P | Omnibox |
| Ctrl/Cmd+Shift+P | AI commands |
| Ctrl/Cmd+/ | Commands / omnibox |
| Ctrl/Cmd+F | Search Workspace |
| Ctrl/Cmd+W | Close active tab |
| Ctrl/Cmd+Shift+T | Reopen closed tab |
| Alt+] / Alt+[ | Next / previous tab |
| Ctrl/Cmd+Alt+] / [ | Next / previous dock panel |
| Ctrl/Cmd+H | Dashboard home |
| Ctrl/Cmd+B | Toggle favorite (in palette) |
| Ctrl+Tab | Quick switcher (apps) |
| Esc | Close overlays |

Catalog source: `navigation/managers/shortcutManager.ts`  
Runtime: `CommandCenterProvider` + `useEnterpriseKeyboard` (FullLayout).

## Global Activity Feed

Merges:

- Workspace activity journal  
- Notification Center  
- Synthetic CRM / workflow / AI signals  

Filters: All · AI · System · CRM · User · Jobs · Notifications · Workflow · Errors · Warnings

## AI Command Center

Shows running / queued / completed agents, provider · voice · MCP · memory probes, model usage, execution time, estimated cost (local demo = $0.00).

## Enterprise Metrics

Live KPI strip: Projects · Clients · Tasks · Revenue · Active AI Agents · Running Workflows · System Health · API Requests.

## Universal Quick Actions

New Client · Project · Task · Workflow · AI Agent · Upload Document · Open Dashboard · CRM · ERP.

Also available via palette Create section and floating **+ Create** (Sprint 27.4).

## Enterprise Status Bar

Persistent bottom bar: Environment · Workspace · User · Runtime · Git branch · Connection · AI · Alerts · Jobs · API · MCP.

## Future extensions

- Server-backed command analytics and favorites  
- WebSocket activity stream  
- Real provider cost metering  
- Voice command mode  
- Customizable shortcut remapping UI  
- Keep-alive multi-module panes inside Command Center

## Related docs

- [SPRINT_27_5_RESULT.md](./SPRINT_27_5_RESULT.md)  
- [SPRINT_27_4_RESULT.md](./SPRINT_27_4_RESULT.md)  
- `src/web/command-center/README.md`
