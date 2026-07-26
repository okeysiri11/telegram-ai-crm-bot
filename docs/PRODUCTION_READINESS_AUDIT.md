# Production Readiness Audit — Sprint 30.2

Complements `ENTERPRISE_PRODUCTION_READINESS.md` (EPD control plane) with a **platform-wide** readiness view.

## Scorecard

| Domain | Ready? | Evidence | Blocker |
|--------|--------|----------|---------|
| Vertical backends (auto/agro/legal/crypto/drone) | **Mostly** | Manifests claim Production Ready / Certified | Ops runbooks + env secrets |
| Platform Builder hubs | **Dev-ready** | Pytest 28.x–30.2 strong | Auth, OpenAPI, HA claims vs memory |
| Enterprise Hub facades | **Partial** | Broad API surface | Contract freeze |
| Identity / RBAC | **Partial** | UI + DB RBAC | Live token path |
| Observability | **Partial** | metrics/health + OBS docs | Unified SLOs |
| OpenAPI / SDK | **Partial** | EAS governance | Coverage gaps |
| Web portals for industries | **No** | No vertical React apps | Web readiness sprint |
| Cafe product | **No** | Catalog only | Product sprint |
| Dual runtime (bot+API) | **Ops gap** | Separate entrypoints | Deploy compose |
| Data migrations | **Present** | Alembic | Release checklist |

## Required before Production (platform)

1. Live authentication on APIs used by web  
2. Prefix ownership + OpenAPI for customer-facing APIs  
3. Explicit deploy topology (API + bot + web + DB)  
4. Secret/config baseline from `.env.example` / `.env.production`  
5. Production readiness gates for chosen pilot vertical (recommend **Automotive**)  
6. Clarify non-goals: Telegram continues; not blocked by web portal absence for bot channels  

## Required before Web (see also Web Readiness Report)

1. Identity Center → API token bridge  
2. Customer / Employee / Owner portal shells on universal modules  
3. Mission Control + Workspace already exist — reuse, don’t rebuild  
4. Industry pages compose capability catalogs — don’t fork PB engines  

## What blocks testing today

| Blocker | Impact |
|---------|--------|
| Header-only PB auth | Cannot simulate real user sessions in web E2E |
| Missing vertical web | Cannot UI-test dealer/trader/lawyer portals |
| Agent stubs | AI E2E unreliable |
| Dual ecosystem confusion | Testers hit wrong API prefix |
| Soft nav routes | False failures / dead links |

## Non-redesign stance

Production hardening **extends** EPD, OBS, ISAM, and existing manifests. No replacement of certified vertical backends.
