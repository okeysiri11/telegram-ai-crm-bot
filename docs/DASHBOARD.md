# Enterprise Live Dashboard

**Sprint:** 27.6  
**App:** `src/web`  
**Package:** `src/live-dashboard/`

## Purpose

Turn `/dashboard` into a **live Enterprise Operating System** surface: auto-updating runtime tiles, reusable enterprise widgets, movable/resizable layouts, role profiles, and an event bus — without redesigning the existing shell.

## Architecture

```
DashboardPage
  └── LiveDashboardShell
        ├── liveDashboardStore (layouts · profile · collapsed · filters)
        ├── dashboardEventBus → liveUpdates + notificationStore
        ├── LiveDashboardDataProvider (shared metrics / health / activity)
        └── LiveWidgetChrome × N
              └── LiveWidgetBody (runtime + enterprise widgets)
```

**Extend only:** reuses `useRuntimeHealth`, `notificationStore`, `activityJournal`, `ENTERPRISE_MODULES`, `TODAY_ITEMS`, and workspace `liveUpdates`. Does not replace Morning Brief, Command Center sections, or legacy `cc-grid`.

## Runtime widgets

| Widget | Updates |
|--------|---------|
| CPU Usage | Local smoothed estimate (browser has no process CPU) |
| Memory Usage | `performance.memory` when available |
| AI Runtime | Soft health probes |
| Connected Providers | Soft health probes |
| MCP | Soft health probes |
| Active Agents | Derived from AI tabs + live tick |
| Background Jobs | Notification job/workflow/task kinds |
| Event Queue | Unread + jobs depth |
| Notifications | Unread count |
| Active Sessions | Workspace tab count |

## Enterprise widgets

System Health · AI Status · Recent Activity · Notifications · Tasks · Projects · CRM Summary · Finance Summary · Knowledge Base · Calendar

Each supports **collapse · refresh · fullscreen · pin · resize (± colSpan) · drag reorder**.

## Profiles

| Profile | Focus |
|---------|--------|
| CEO | Health, finance, CRM, AI |
| Manager | Tasks, projects, activity |
| Sales | CRM, calendar, pipeline |
| Developer | CPU, memory, MCP, queue, agents |
| Finance | Finance, CRM, projects |
| Administrator | Full catalog |

## Layout engine

- CSS 4-column grid (`eld-grid`)
- Drag-and-drop reorder between widgets
- Column span 1–4 via chrome controls
- Multiple named layouts (`Save layout`)
- `Restore profile` resets to profile default
- Persistence key: `ews_live_dashboard_v1`

## Event bus

`dashboardEventBus` listens to:

- `liveUpdates` (websocket / event_bus / notification_center / poll)
- Notification store deltas (unread, jobs, errors)
- 15s poll tick

Widgets re-render via store `tick` + shared data context (no duplicated pollers per tile).

## Persistence

Saved: widget positions (order), colSpan, collapsed, pinned, profile, active layout, activity filter, custom layouts.

## Keyboard / chrome

Widget chrome buttons: − + ↻ Pin Fullscreen Collapse. Drag handle = widget header.

## Future

- Real host CPU via OBS/agent metrics API  
- Pixel-perfect freeform drag canvas  
- Shared layout sync across tenants  
- Server-backed layout profiles  

## Related

- [SPRINT_27_6_RESULT.md](./SPRINT_27_6_RESULT.md)  
- [COMMAND_CENTER.md](./COMMAND_CENTER.md)  
- [SPRINT_27_5_RESULT.md](./SPRINT_27_5_RESULT.md)
