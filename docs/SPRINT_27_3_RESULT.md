# Sprint 27.3 — Enterprise Platform Core Modules

**Phase:** 3 — Interactive Workspace & Functional Modules  
**App:** `src/web` · sprint `27.3`

## Implemented

1. **Workspace Manager** (`src/workspace-engine/`) — open modules, tabs, active workspace, history, session restore  
2. **Multi-tabs** — open / switch / close / pin / persist (`ews_workspace_session_v1`)  
3. **Command Palette** — Ctrl/Cmd+K; Open CRM/ERP/AI Studio/Documents/Analytics/Marketplace/Settings/Knowledge; Search; Create Client/Project/Task/…  
4. **Global Search** — index includes hubs + commands (`/search` + palette)  
5. **Notification Center** — info/warning/success/error/system/ai/runtime (+ legacy kinds); queue + history  
6. **Activity journal** — navigate/search/create/ai/error/login/system  
7. **Quick Actions** panel — create client/project/document/agent/workflow/knowledge  
8. **Dashboard widgets** — System/Runtime/AI/Queue/Projects/CRM/Knowledge/Analytics/Activity  
9. **Module Framework** — Overview · Statistics · Recent Activity · Quick Actions · Status · Configuration (+ skeleton/error/retry)  
10. **Settings** — Theme · Language · Workspace · Notifications · Profile · Session  
11. **Profile** — avatar · role · org · last login · active session  
12. **Session restore** — tabs + theme + last module + route sync  

## Temporary data

Status probes when API offline; activity/notification seeds; module stats from catalog.

## Sprint 27.4 recommendations

- Live Runtime/ISAM binding for widgets  
- Keep-alive tab content (no remount)  
- Server-backed notification queue  
- Drag-reorder tabs  
- Deep create forms (not query-action hubs only)

## Verify

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **74 passed** |
| build | OK |
| dev | `npm run dev` → http://localhost:5180 |

```bash
cd src/web && npm install && npm run lint && npm test && npm run build && npm run dev
```
