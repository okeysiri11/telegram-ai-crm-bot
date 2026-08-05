# Sprint 30.8 Result — Enterprise Business Modules

**Priority:** HIGHEST  
**Status:** Complete  
**Date:** 2026-08-01  
**Track:** Enterprise Web (`src/web`)

> **Naming:** Platform Builder / Beauty also use Sprint **30.8** docs (`BEAUTY_PILOT_30_8.md`, `RELEASE_NOTES_30_8.md`). This RESULT is the **Enterprise Business Modules** web track only.

## Mission

Replace remaining business-module placeholders with operational pages bound to existing APIs, runtime, and navigation.

## Delivered

| Module | Route | Implementation |
|--------|-------|----------------|
| CRM | `/crm` | Clients, companies, contacts, leads, deals, pipeline, activity, notes, attachments · Auto CRM API |
| Projects | `/projects` | Projects, kanban, tasks, milestones, timeline, docs, team |
| Knowledge | `/knowledge` | KB, wiki, docs, search, categories, tags, AI search · EKP hydrate |
| Calendar | `/calendar` | Day/week/month, meetings, tasks, reminders |
| Notifications | `/notifications` | Inbox, activity, history, unread, priority · comms hydrate |
| Drive | `/documents` | Browser, upload, preview, categories, search, recent |
| Marketplace | `/marketplace` | Installed / available / updates / details · Solution Hub |
| AI Studio hub | catalog `ai_studio` | Agents, prompts, workflows, tasks, history, logs |
| Owner Dashboard | `/owner` | Live metrics via `deriveOwnerMetrics` |

## Architecture

- Package: `src/web/src/enterprise-business/`
- Hubs resolved in `ModulePageById` (extends catalog routing — no parallel router)
- Persistence: tenant workspace cache when APIs unavailable (same pattern as marketplace install)
- Permissions: `PermissionGuard` + existing RBAC / tenant headers on `apiFetch`

## Docs

`CRM.md` · `PROJECTS.md` · `KNOWLEDGE.md` · `CALENDAR.md` · `NOTIFICATIONS.md` · `FILES.md` · `MARKETPLACE.md` (section) · `AI_STUDIO.md` (section) · `OWNER_DASHBOARD.md` · this file · `ARCHITECTURE_MAP.md`

## Quality

```bash
cd src/web && npm run lint && npm test && npm run build
```
