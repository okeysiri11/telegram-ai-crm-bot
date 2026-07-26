# API Status — Sprint 30.4

Validation for modules connected through the Web shell. Ownership remains as published in [API_OWNERSHIP_REGISTRY.md](./API_OWNERSHIP_REGISTRY.md).

## Contract posture

| Area | Status | Notes |
|------|--------|-------|
| API Contracts | Stable ownership | No new prefixes in 30.4 |
| DTOs | Existing vertical / PB DTOs | Shell does not invent DTOs |
| Permissions | Header bridge ready | `Authorization`, `X-Tenant-Id`, `X-Organization`, `X-Workspace`, `X-Role-Id` |
| Events | Existing hub / visual buses | Unchanged |
| Responses | JSON via existing handlers | Unchanged |
| Error Handling | OBS error logs + ErrorBoundary | Web client reports to OBS |
| OpenAPI consistency | Deferred freeze (P0 backlog) | Automotive freeze still next |

## Connected prefixes (readiness for pilots)

| Prefix | Module shell | Live UI binding |
|--------|--------------|-----------------|
| `/api/auto/v1` | `/workspace/auto` | Partial — next sprint workflows |
| `/api/agro/v1` · agro-enterprise | `/workspace/agro` | Shell |
| `/api/legal-enterprise/v1` | `/workspace/legal` | Shell |
| `/api/crypto-enterprise/v1` | `/workspace/crypto` | Shell |
| `/api/finance-enterprise/v1` | `/workspace/finance` | Shell |
| `/api/platform-builder/v1` | PB hubs / Mission Control | Operational |
| `/api/enterprise-obs/v1` | Telemetry client | Operational |
| `/api/enterprise-eic/v1` · ISAM | Identity health / future JWT | Bridge path wired |

## Web client helpers

- `apiFetch` — identity-aware fetch  
- `telemetry` — metrics (`api`, `active_users`, `active_sessions`, …) + logs (`application`, `audit`, `error`, `ai`)  
- Health probes remain on `hub.ts` (EWF, EDS, EIC, EWS, ENP, OBS)  

## Explicitly unchanged

CRM deprecation schedule, ecosystem package separation, and Mission Control aggregation APIs.
