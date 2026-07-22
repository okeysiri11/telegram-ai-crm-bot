# API Reference


---
[[INDEX]] · [[PLATFORM_CORE]] · [[ARCHITECTURE]] · [[API_REFERENCE]]


## Overview
HTTP API surface for Platform Core, Ecosystem, and vertical applications as mounted in `api/server.py`.

## Architecture
- System probes: `/liveness`, `/readiness`, `/health`, `/system/db-health`, `/metrics`
- Frozen public Platform API: `/api/v1` (+ legacy `/v1`)
- Management: `/management/v1`
- Ecosystem + apps: versioned `/api/<domain>/v1`

## Components

| Surface | Prefix | Notes |
|---------|--------|-------|
| Platform public | `/api/v1` | Contract 1.0.0 |
| Platform management | `/management/v1` | Ops / admin |
| Ecosystem | `/api/ecosystem/v1` | Identity, assistant, governance |
| Agro | `/api/agro/v1` | Also mobile/partner/internal/webhooks |
| Port | `/api/port/v1` | Also internal/webhooks |
| Auto | `/api/auto/v1` | Also mobile/partner/portal/internal/webhooks |
| Drone | `/api/drone/v1` | Also `/internal/drone/v1` |
| Legacy CRM gateway | `/api/auth`, `/api/leads`, … | Unversioned Telegram CRM API |

### Drone foundation endpoints (Sprint 11.1)
`/health`, `/registry/*`, `/projects/*`, `/engineering/*`, `/firmware/*`, `/missions/*`, `/telemetry/*`, `/inventory/*`, `/documentation`, `/ai/*`

## Relationships
- App handlers live under `applications/*/api/`
- Bridges authenticate/enrich where middleware requires — [[SECURITY]]
- Diagram: [[diagrams/DATA_FLOW]]

## APIs
This page **is** the API map. Deeper OpenAPI-style detail remains in repository `docs/api.md` and per-app docs.

## Future roadmap
OpenAPI generation per application and unified developer portal ([[ROADMAP]]).

## Responsibilities
Document and navigate this concern within the Obsidian living vault (Knowledge 1.1).

## Interfaces
Wiki links, dashboards, and registries. Runtime interfaces described where applicable.

## REST APIs
See [[registries/API_REGISTRY]] and [[API_REFERENCE]] when this page owns HTTP surfaces; otherwise N/A.

## Events
Domain or documentation events as applicable; see related sprint pages.

## References
Repository `docs/`, manifests, [[standards/DOCUMENTATION_STANDARDS]].

## Related pages
[[INDEX]] · [[DASHBOARD]] · [[ROADMAP]] · [[registries/COMPONENT_REGISTRY]]
