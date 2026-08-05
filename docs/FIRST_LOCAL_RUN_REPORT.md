# First Local Run Report — Sprint 32.6A

**Date:** 2026-08-02  
**Machine:** macOS (darwin) · Node 24 · Python 3.14 venv · **Docker: not installed**

## Collision

Sprint **32.6** also = AI Team Collaboration. This report is the **Local Launch Recovery** track only.

## Services started (verified this session)

| Service | Port | Status | Notes |
|---|---|---|---|
| PostgreSQL (local) | 5432 | **up** | `pg_isready` accepts connections |
| Redis | 6379 | **down** | Optional; `REDIS_REQUIRED=false` |
| Docker Compose | — | **unavailable** | `docker` command not found |
| Python API (`run_api_local.py`) | 8080 | **up** | `/liveness` → 200 |
| Enterprise Web (Vite) | 5180 | started via `npm run dev` / `dev:all` | |
| CRM worker | — | **skipped** | Set `ADOS_LOCAL_CRM_WORKER=1` to enable |
| WebSocket | — | **off** | `VITE_SOCKET_URL` empty |
| platform_console | — | not required for Owner demo | |

## Health

| Endpoint | Result |
|---|---|
| `GET /liveness` | **200** — process alive |
| `GET /health` | **503** — readiness suite reports unhealthy (Redis down / DB schema gaps such as missing `tenants` FK target) |
| Vite `/api` proxy | Returns structured `api_unavailable` JSON on connection errors (no raw ECONNREFUSED crash) |

## Missing dependencies (this host)

- Docker / Docker Compose
- `redis-cli` / Redis server
- Full DB migrations for all FKs (known schema debt)

## Known issues

1. **`/health` 503** while API is usable for demo — prefer `/liveness` for “is the API up?”.
2. **Without Redis**, workers and some readiness checks fail; demo auth + Vite plugins still allow Owner/City.
3. **Schema gaps** (e.g. `events.tenant_id` → `tenants`) can surface when enabling CRM worker.
4. Root `npm run dev` still points at **platform_console** (historical). Use **`npm run dev:all`** for Enterprise Web + API.
5. `INSTALLATION.md` previously cited port 5173 — corrected to **5180** in Local Run docs.

## Final launch command

```bash
# from repo root (after venv + pip install -r requirements.txt + npm install --prefix src/web)
npm run dev:all
```

Then open:

- http://127.0.0.1:5180/login — `owner@demo.corp` / `demo`
- http://127.0.0.1:5180/owner
- http://127.0.0.1:5180/city
- http://127.0.0.1:5180/platform-builder/runtime
- http://127.0.0.1:8080/liveness

## Artifacts

- `docs/LOCAL_RUN.md`
- `scripts/dev_all.mjs`
- `scripts/run_api_local.py`
- `src/web/vite.config.ts` (proxy error handling)
- `src/web/.env.development`
- Root `package.json` scripts: `dev:all`, `dev:api`, `dev:web`, `dev:infra`
