# Enterprise Workspace

**Sprint:** 30.7  
**Surface:** `src/web` Enterprise Shell

## Purpose

A usable Enterprise Workspace where every visible navigation element opens a real module — no placeholders, dead buttons, or empty pages.

## Shell

| Layer | Implementation |
|-------|----------------|
| Left navigation | `ENTERPRISE_RU_SIDEBAR` → `Sidebar.tsx` |
| Top bar | `TopNavigation.tsx` — search, org, role, notifications, AI |
| Breadcrumbs | `Breadcrumbs.tsx` + `BREADCRUMB_LABEL_RU` |
| Owner Mode | `OWNER_RU_NAV` + `/owner` |
| God Mode | `/platform-builder/god-mode` |
| Command Palette | Ctrl/Cmd+K via `CommandCenterProvider` |

## Wired modules

| Module | Route |
|--------|-------|
| CRM | `/crm` |
| ERP | `/erp` |
| Knowledge | `/knowledge` |
| AI Runtime / Agents | `/ai-agents` |
| Production Studio | `/production-studio` |
| Marketplace | `/marketplace` |
| Analytics | `/analytics` |
| Notifications | `/notifications` |
| Documents | `/documents` |
| Calendar | `/calendar` |
| Finance | `/workspace/finance` |
| Tasks | `/tasks` |
| Users | `/identity/users` |
| Settings | `/settings` |
| City | `/city` |

Canonical list: `src/web/src/enterprise-workspace/workspaceRoutes.ts`.

## Role dashboards

| Role | Home |
|------|------|
| Owner | `/owner` |
| Administrator | `/admin` |
| Client | `/dashboards/client` |
| Dealer | `/dashboards/dealer` |
| Manager / Employee | `/dashboard` |

## Ops pages (30.7)

- `CalendarPage`, `TasksPage`, `NotificationsPage` — `enterprise-workspace/WorkspaceOpsPages.tsx`
- `AdminDashboardPage` — `dashboard/AdminDashboardPage.tsx`

## Related docs

- [ENTERPRISE_NAVIGATION.md](./ENTERPRISE_NAVIGATION.md)
- [OWNER_WORKSPACE.md](./OWNER_WORKSPACE.md)
- [COMMAND_PALETTE.md](./COMMAND_PALETTE.md)
- [SPRINT_30_7_RESULT.md](./SPRINT_30_7_RESULT.md)
