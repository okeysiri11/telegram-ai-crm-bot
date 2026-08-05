# Enterprise City Runtime

Unified operating environment connecting every ADOS module into one intelligent ecosystem — Sprint **37.0**.

Canonical SoR: **`platform_orchestrator`** (`city_runtime_*`). Do **not** create `platform_city`.

Spatial map adapter remains: `src/web/src/enterprise-city/` (`/enterprise-city`, `/city`).

## Kernel

| Capability | API / module |
|------------|--------------|
| Global Service Registry | `GET /api/platform/services` |
| Global Navigation | `GET /api/platform/navigation` |
| Universal Search | `/api/search` |
| Universal Command Palette | `GET /api/platform/palette` |
| Cross-module Routing | `POST /api/platform/route` |
| Global Notifications | `/api/platform/notifications` |

## Unified Workspace

CRM · ERP · AI Runtime · Multi-Agent · Project Memory · Context Engine · Workflow · Creative Factory · Voice · Analytics · Knowledge Base

`GET /api/platform/workspace`

## Cross-Module Communication

- Shared context / memory — platform sessions
- Shared events — `POST /api/platform/events`
- Shared permissions — session RBAC lists
- Shared user sessions — `POST /api/platform/sessions`

## Enterprise Dashboard

Live KPIs, active agents, workflows, projects, notifications, AI recommendations, platform health, business analytics.

`GET /api/dashboard`

## Command Center

Natural language · voice · AI execution · workflow execution · service execution

`POST /api/platform/command`

## REST

| Prefix | Scope |
|--------|--------|
| `/api/platform/*` | Kernel, sessions, health, command, integrations |
| `/api/dashboard/*` | Executive dashboard |
| `/api/search/*` | Global semantic search |
| `/management/v1/platform/*` | Management dual-prefix |
| `/city`, `/city/simulate` | Seed aliases |

## Database

Alembic `t3n456789012` (revises `s2m345678901`):

- `platform_registry`
- `platform_sessions`
- `platform_metrics`
- `platform_health`
- `platform_usage`
- `platform_configuration`

ORM: `database/models/enterprise_city_runtime.py`

## UI

`/platform` — Enterprise Dashboard, Global Search, Platform Health, Service Registry, Activity Center, Command Center, Platform Settings.

## Production readiness

`GET /api/platform/readiness` — integration, smoke, load, regression, security, API checks.

## Modules

| File | Role |
|------|------|
| `platform_orchestrator/city_runtime_models.py` | Domain models |
| `platform_orchestrator/city_runtime_engine.py` | Kernel + dashboard + search + commands |
| `platform_orchestrator/city_runtime_service.py` | Façade + integrations |
| `platform_orchestrator/city_runtime_router.py` | HTTP |

## Verify

```bash
.venv/bin/python -m pytest tests/test_enterprise_city_runtime_37_0.py -vv
```
