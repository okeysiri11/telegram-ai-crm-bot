# LOCAL_RUN — Zero-Touch Local Launch (Sprint 32.6B)

**Track:** First Local Launch / Zero-Touch  
**Collision:** Product Sprint **32.6** = AI Team Collaboration (`AI_TEAM_COLLABORATION_32_6.md`) — preserved.  
**Goal:** Clone → one command → open Owner Dashboard in the browser.

**Success report:** [`FIRST_SUCCESSFUL_LOCAL_RUN.md`](./FIRST_SUCCESSFUL_LOCAL_RUN.md)

## Prerequisites

| Tool | Version | Required |
|---|---|---|
| Node.js | **≥ 20** (tested 24.x) | Yes |
| npm | comes with Node | Yes |
| Python | **≥ 3.11** (venv recommended) | Yes for API |
| PostgreSQL | 14+ listening on `:5432` | Recommended |
| Redis | 7+ on `:6379` | Optional locally (`REDIS_REQUIRED=false`) |
| Docker Compose | optional | Starts Postgres+Redis when Docker exists |

### Without Docker

This machine may not have Docker. Local launch still works when:

1. PostgreSQL is already running locally (or you accept API degradation + **demo auth**).
2. `REDIS_REQUIRED=false` in `.env` (default for local).
3. You use `npm run dev:all` which detects missing Docker and continues.

## Backend services the frontend needs

| Service | Port | Role |
|---|---|---|
| **Enterprise Web (Vite)** | `5180` | SPA — login, Owner, City, AI Runtime |
| **Python aiohttp API** | `8080` | `/api/*`, `/management/*`, `/health`, `/liveness` |
| **PostgreSQL** | `5432` | Persistence for hub/ISAM/CRM |
| **Redis** | `6379` | FSM / workers (optional in local demo) |
| **Vite local plugins** | (in-process) | Demo auth, EBN/EDC/City Viz stubs when Hub paths bypass proxy |
| WebSocket | optional | `VITE_SOCKET_URL` empty = off |
| Workers / CRM bus | optional | Enable with `ADOS_LOCAL_CRM_WORKER=1` |
| platform_console / TS kernel | `:5173` etc. | **Not** required for Owner demo (separate Control Center) |

Proxy: `src/web/vite.config.ts` → `VITE_API_PROXY` (default `http://127.0.0.1:8080`).

## Environment variables

### Root `.env` (copy from `.env.example`)

```bash
ENVIRONMENT=development
POSTGRES_ONLY=true
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_ecosystem
REDIS_URL=redis://localhost:6379/0
REDIS_REQUIRED=false
API_HOST=127.0.0.1
API_PORT=8080
JWT_SECRET=<long-random-string>
IAM_JWT_SECRET=<same-or-stronger>
# BOT_TOKEN optional for API-only local mode
```

### `src/web/.env.development` (shipped)

```bash
VITE_DEMO_AUTH=true
VITE_API_PROXY=http://127.0.0.1:8080
VITE_TELEMETRY_ENABLED=false
```

## Exact startup order

1. **Infra** — Docker `postgres`+`redis` **or** local Postgres (Redis optional).
2. **Python venv** — `python3 -m venv venv && ./venv/bin/pip install -r requirements.txt`
3. **Web deps** — `npm install --prefix src/web`
4. **API** — `scripts/run_api_local.py` on `:8080`
5. **Web** — Vite on `:5180`
6. Open browser → login → Owner / City

## One-command launch

From repo root:

```bash
npm run dev:all
```

Equivalent:

```bash
node scripts/dev_all.mjs
```

This will:

1. Detect Docker; if present, `docker compose up -d postgres redis`
2. If Docker missing, continue with local Postgres / optional Redis (`REDIS_REQUIRED=false`)
3. Run `alembic upgrade head` via `scripts/ensure_local_schema.py`
4. Start API (`scripts/run_api_local.py`) — migrations also run inside the API process
5. Start Enterprise Web (`src/web` Vite `:5180`)

Skip migrations: `ADOS_SKIP_MIGRATIONS=1 npm run dev:all`  
Abort on migrate failure: `ADOS_FAIL_ON_MIGRATE=1`

### Manual split

```bash
npm run dev:api    # API only
npm run dev:web    # Vite only
npm run dev:infra  # Docker postgres+redis (when Docker exists)
```

## Demo login (no Hub required)

| Field | Value |
|---|---|
| URL | http://127.0.0.1:5180/login |
| Email | `owner@demo.corp` |
| Password | `demo` |
| Tenant | `demo-corp` |

Then: First Entry wizard (if needed) → **Owner** `/owner` → **City** `/city` → **AI Runtime** `/platform-builder/runtime`.

## Verify

```bash
curl -s http://127.0.0.1:8080/liveness
curl -s http://127.0.0.1:8080/health
# open http://127.0.0.1:5180/login
```

- `/health` may return **503** if Redis/DB readiness checks fail — `/liveness` **200** means API process is up.
- Vite proxy returns JSON `api_unavailable` instead of crashing on `ECONNREFUSED`.

## Related

[`FIRST_LOCAL_RUN_REPORT.md`](./FIRST_LOCAL_RUN_REPORT.md) · [`INSTALLATION.md`](./INSTALLATION.md) · [`CLOSED_BETA_GUIDE.md`](./CLOSED_BETA_GUIDE.md)
