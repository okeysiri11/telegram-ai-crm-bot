# Sprint 37.0 Result — Enterprise City Runtime

## Summary

Enterprise City Runtime delivered **inside** canonical SoR `platform_orchestrator` (no `platform_city` package). Spatial map remains the presentation adapter under `src/web/src/enterprise-city/`.

## Delivered

| Area | Result |
|------|--------|
| Kernel | Registry, navigation, search, palette, routing, notifications |
| Workspace | CRM, ERP, AI, Agents, Memory, Context, Workflow, Creative, Voice, Analytics, Knowledge |
| Cross-module | Shared context/memory/events/permissions/sessions |
| Dashboard | KPIs, agents, workflows, projects, notifications, recommendations, health, analytics |
| Global Search | clients, projects, documents, tasks, workflows, memories, agents, media, reports |
| Command Center | NL, voice, AI, workflow, service execution |
| REST | `/api/platform`, `/api/dashboard`, `/api/search`, `/management/v1/platform` |
| DB | Alembic `t3n456789012` + `database/models/enterprise_city_runtime.py` |
| UI | `/platform` (+ section routes) |
| Integrations | Sprint 1–36.9 modules via registry + probe façades |
| Production | readiness checks (integration/smoke/load/regression/security/API) |
| Docs | `ENTERPRISE_CITY_RUNTIME.md`, `PLATFORM_ARCHITECTURE.md` |
| Tests | `tests/test_enterprise_city_runtime_37_0.py` |

## Architecture

| Layer | Location |
|-------|----------|
| Control plane | `platform_orchestrator/city_runtime_*` |
| Spatial UI | `src/web/src/enterprise-city` |
| Console UI | `src/web/src/platform-console` |

## Verify

```bash
.venv/bin/python -m pytest tests/test_enterprise_city_runtime_37_0.py -vv
```
