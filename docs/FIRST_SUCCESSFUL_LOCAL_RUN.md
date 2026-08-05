# First Successful Local Run — Sprint 32.6B

**Track:** Zero-Touch Local Launch  
**Collision:** Product Sprint **32.6** = AI Team Collaboration — preserved.  
**Verified:** 2026-08-02 on macOS (Docker absent; local PostgreSQL; Redis absent)

## Exact startup command

```bash
# one-time (clean machine)
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
npm install --prefix src/web
cp -n .env.example .env   # set DATABASE_URL / JWT secrets as needed

# every time
npm run dev:all
```

Then open:

**http://127.0.0.1:5180/login**  
Credentials: `owner@demo.corp` / `demo`

## Startup time (this machine)

| Phase | Approx. |
|-------|---------|
| Infra probe (Docker / ports) | &lt; 1s |
| Alembic `upgrade head` | ~12s (first run; near-instant when current) |
| API bind + event handlers | ~10–15s |
| Vite ready | ~5–10s |
| **Total cold `dev:all` to browser** | **~25–40s** |

## Services started

| Service | Port | How |
|---------|------|-----|
| PostgreSQL | `5432` | Local (or Docker when available) |
| Redis | `6379` | Optional — auto `REDIS_REQUIRED=false` when absent |
| Python API (`run_api_local.py`) | `8080` | Auto-migrates schema, then serves HTTP |
| Enterprise Web (Vite) | `5180` | Demo auth plugin + API proxy |

Not required for Owner / City demo: Telegram bot, CRM worker, platform_console, TS kernel.

## Verified routes

| Route | HTTP | Notes |
|-------|------|-------|
| `/login` | 200 | Demo form pre-fills owner |
| Demo login `POST /api/enterprise-demo-auth/v1/login` | 200 | Vite local plugin |
| `/owner` | 200 | Owner Dashboard shell |
| `/city` | 200 | Enterprise City |
| `/platform-builder/runtime` | 200 | AI Runtime |
| `GET :8080/liveness` | 200 | Process alive |
| `GET :8080/health` | 200 | `ok=true`, `ready=true`, status may be `degraded` without Redis |

## Known limitations

1. **Redis optional** — FSM / CRM worker / full bot path need Redis; Owner demo does not.
2. **Telegram optional** — no `BOT_TOKEN` → API-local mode; Telegram check skipped in non-production.
3. **CRM worker off** — enable with `ADOS_LOCAL_CRM_WORKER=1` after Redis is up.
4. **Docker optional** — without Docker, Postgres must already listen on `:5432`.
5. **Health may be `degraded`** — Redis / scheduler / API self-probe soft-fail; still HTTP 200 when `ready`.
6. **Clean machine still needs** Python venv + `pip install` + `npm install --prefix src/web` once (documented above). `dev:all` installs web deps if missing and runs migrations automatically.

## Final launch command

```bash
npm run dev:all
```

Related: [`LOCAL_RUN.md`](./LOCAL_RUN.md) · [`SPRINT_32_6B_RESULT.md`](./SPRINT_32_6B_RESULT.md) · [`FIRST_LOCAL_RUN_REPORT.md`](./FIRST_LOCAL_RUN_REPORT.md)
