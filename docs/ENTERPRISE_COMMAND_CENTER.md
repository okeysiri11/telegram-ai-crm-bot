# Enterprise Command Center

Sprint **26.6** / Platform **v9.0.5** — Enterprise Command Center & Productivity Platform.

Comparable productivity surface to Microsoft 365, Linear, Atlassian and Notion — integrated with the existing Enterprise Platform (Workspace, Navigation, Dashboards, AI, Marketplace, RBAC).

## Architecture

```
platform_enterprise_command_center/     # library (search, actions, AI, analytics)
applications/enterprise_hub/
  command_center_platform/              # hub suite + API handlers
  command_center/enterprise_command.py  # bridge to 26.6 suite (20.12 ECC retained)
src/web/command-center/                 # React UI (palette, omnibox, productivity hub)
```

Legacy Sprint 20.12 executive Command Center remains at `/api/enterprise-ecc/v1`.

## API

Base: **`/api/enterprise-command/v1`**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Readiness |
| POST | `/bootstrap` | Bootstrap suite |
| GET | `/inventory` | Architecture inventory |
| GET | `/dashboard` | Command dashboard |
| GET/POST | `/search` | Omnibox / fuzzy search |
| POST | `/execute` | Permission-gated action |
| POST | `/ai` | AI command execution |
| GET | `/suggestions` | Smart suggestions |
| GET/POST | `/context` | Session context engine |
| GET | `/productivity` | Productivity hub widgets |
| GET | `/analytics` | Command analytics |
| GET | `/navigation-index` | Central nav registry |
| POST | `/permissions` | RBAC validation |

## Frontend

Path: `src/web/command-center/`

- `UniversalCommandPalette` — Ctrl/Cmd+K
- `Omnibox` — Ctrl+P / Ctrl+/
- AI mode — Ctrl+Shift+P
- Productivity Hub — `/command-center`
- Integrated via `CommandCenterProvider` in shell `Providers.tsx`
- Navigation chrome bridges to the same palette

## Backend

- Library: `platform_enterprise_command_center.facade.CommandCenterLibrary`
- Suite: `applications.enterprise_hub.command_center_platform.CommandCenterPlatformSuite`
- Store buckets: `ecc2_*`

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl/Cmd+K | Universal Command Palette |
| Ctrl+P | Omnibox |
| Ctrl+Shift+P | AI Command Center |
| Ctrl+Space | Open palette |
| Ctrl+/ | Omnibox |
| Esc | Close |
| Enter | Execute |
| ↑↓ | Navigate |
| Tab / Shift+Tab | Switch modes |

## AI Commands

Natural language intents map to actions: Open CRM/ERP/Beauty/Auto/Agro/Marketplace/Dashboard, Find Client/Employee, Create Customer/Invoice, Generate Weekly Report, Launch Workflow, Run Automation, Mass Update, Summarize Workspace.

## Navigation Index

Central registry indexes applications, modules, dashboards, pages, routes, AI agents, workflows, marketplace, knowledge, CRM, ERP, reports, analytics, settings, widgets.

## Permissions

Before execution: RBAC, tenant isolation, workspace access, organization access, audit log.

## Analytics

Tracks command usage, execution time, AI usage, success rate, errors, popular/unused commands, recommendations. Surfaced on Productivity Hub dashboard.

## Integrations

Workspace · Dashboard · Navigation · AI Platform · Marketplace · Identity Center · Design System
