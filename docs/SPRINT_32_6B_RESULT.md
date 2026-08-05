# Sprint 32.6B — Zero-Touch Local Launch

**Collision:** Product Sprint **32.6** = AI Team Collaboration (`AI_TEAM_COLLABORATION_32_6.md`) — docs untouched.  
**Prior:** Sprint **32.6A** First Local Launch Recovery.

## Objective

One command brings API + Web + schema to a state where a new developer opens `/login` and reaches Owner Dashboard / Enterprise City without manual schema or Redis fixes.

## Root cause fixed

`Event.tenant_id` → `tenants.id` FK failed at flush because `Tenant` was not registered on `Base.metadata`.

**Fix:** side-import `multi_company` + `multi_tenant_foundation` from `crm_events.py` / `users.py`; prioritize those modules in `migration_models.py`.

## Deliverables

| Item | Path |
|------|------|
| Auto migrate | `scripts/ensure_local_schema.py` · called from `run_api_local.py` + `dev_all.mjs` |
| Local API | `scripts/run_api_local.py` — forces `REDIS_REQUIRED=false`, runs Alembic |
| Orchestrator | `scripts/dev_all.mjs` — infra → migrate → API → Vite |
| Redis policy | ConfigurationCenter: production always requires Redis; development respects `REDIS_REQUIRED` (default false) — no longer OR with `POSTGRES_ONLY` |
| Health soft-fail | Optional Redis / missing Telegram / idle scheduler do not block `/health` in non-production |
| Success report | [`FIRST_SUCCESSFUL_LOCAL_RUN.md`](./FIRST_SUCCESSFUL_LOCAL_RUN.md) |

## Verification (this machine)

- `GET /liveness` → 200  
- `GET /health` → 200 (`ok`, `ready`; Redis degraded)  
- Demo login → 200 (`owner@demo.corp` / `demo`)  
- `/login`, `/owner`, `/city`, `/platform-builder/runtime` → 200  

## Command

```bash
npm run dev:all
```
