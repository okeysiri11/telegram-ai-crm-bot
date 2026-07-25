# Enterprise Navigation

Sprint **26.7** / Platform **v9.0.6** — Enterprise Navigation, Global Search & Workspace Federation.

Transforms the platform into a unified workspace where every module, application, vertical, AI agent and workflow is instantly discoverable.

## Architecture

```
platform_enterprise_navigation/          # library
applications/enterprise_hub/navigation/  # hub suite + API
src/web/navigation/                      # React UI
```

Legacy Sprint 26.5 ENP API remains at `/api/enterprise-enp/v1`.

## API

Base: **`/api/enterprise-navigation/v1`**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Readiness |
| POST | `/bootstrap` | Bootstrap suite |
| GET | `/inventory` | Architecture inventory |
| GET | `/dashboard` | Navigation dashboard |
| GET | `/global` | Global navigation sections |
| GET | `/workspaces` | Federated workspaces |
| POST | `/workspaces/switch` | Switch workspace |
| GET | `/registry` | Application registry |
| GET/POST | `/search` | Global fuzzy search |
| GET/POST | `/favorites` | Smart favorites |
| GET | `/history` | Recent history |
| GET | `/breadcrumbs` | Dynamic breadcrumbs |
| POST | `/quick-switch` | Ctrl+Tab switcher |
| GET | `/analytics` | Navigation analytics |
| POST | `/permissions` | RBAC validation |

## Frontend

Path: `src/web/navigation/`

- Global navigation dashboard `/navigation`
- Workspace federation switcher
- Application registry
- Global search
- Smart favorites & recent history
- Quick Switcher (`Ctrl+Tab`)
- Enterprise breadcrumbs
- Navigation analytics

## Application Registry

Automatically registers every application with icon, name, status, owner, permissions, version, health, and last update.

Personal · Organization · Department · Project · Customer · AI · Temporary

## Security

RBAC · Workspace Isolation · Tenant Isolation · Organization Isolation

## Integrations

Workspace · Command Center · Dashboard · AI Platform · Marketplace · Identity Center
