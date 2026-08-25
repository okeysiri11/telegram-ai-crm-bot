# Sprint 14 — Production Verification + Runtime Hardening

## Baseline

`61aa197f6edd1f2723210dcf57221c0f044f56a0` on `develop` (Sprint 13.1 durable Render path).
Local HEAD matched `origin/develop`. Worktree was clean. Alembic head `s8n901234567` (count 1).

## Production architecture (verified live)

Durable production is **Render**, not a laptop tunnel.

| Layer | Implementation |
|---|---|
| Public host | `https://ados-web.onrender.com` (Render web `ados-web`, Frankfurt, free) |
| Blueprint | `render.yaml` — `autoDeployTrigger: checksPass` on `develop` |
| Web image | `Dockerfile.web` → `scripts/run_production_web.py` |
| Database | Render managed PostgreSQL `ados-postgres` (asyncpg, PostgreSQL 18.4) — CRM source of truth |
| Redis | Render Key Value `ados-redis` (required by production config policy) |
| Frontend | Same-origin SPA from `src/web/dist` (`ADOS_SERVE_WEB=true`, `api/web_static.py`) |
| Backend | Same process: `/api`, `/management`, `/liveness`, `/readiness`, `/health` |
| 3D city | SPA `/enterprise-city` and browser `/city`; tiles `/assets/odessa/*.glb` + `odessa_manifest.json` |
| Deploy flow | push `develop` → Production Gate GitHub check → Render deploys that SHA → `/liveness` health gate |
| Preview (not production) | `scripts/start_public_host.py` Cloudflare Quick Tunnel |

Telegram polling is **not** this service (`ADOS_TELEGRAM_REQUIRED=false` in the blueprint). The bot remains a separate run target. A dashboard `BOT_TOKEN` may still make readiness telegram checks healthy.

## What this sprint hardened

1. **Production Bearer fail-closed.** `platform_bridge.authenticate_request` no longer treats every `Bearer *` as authenticated. The previous hole was `SessionManager.validate` returning `bool(session_id)` when the identity store is unavailable — so `Authorization: Bearer not-a-real-token` returned CRM manager JSON on the live host. Production/staging now require a real session or JWT. Local/CI `Bearer test` is unchanged.
2. **Browser `/city` serves the SPA.** `/city` remains an authenticated city-runtime API for JSON clients. `Accept: text/html` navigations receive `index.html` so deep links work.
3. **Readiness persistence probe.** After writing `SystemHealth` rows, readiness reports `{write, readback, history_count, source: postgres}` with no connection secrets.
4. **`startup_validated` follows actual readiness.** Once `/readiness` is ready, liveness reports `startup_validated=true` (previously stuck false after a cold-start self-probe).
5. **Redis hostname stripped** from public health payloads (`reachable` only).
6. **Production SPA defaults** no longer bake `http://localhost:5678` / `:4000` for n8n/LiteLLM.
7. **CI** Production Gate / Foundation / Verify cover Sprint 14 tests, city assets, forged-bearer 401, and persistence.

No Alembic migration. No second CRM store. Sprint 7–13 CRM routes preserved (auth tightened, not weakened).

## Architectural decisions

- **Fail closed in production rather than inventing a new auth stack.** Reuse IAM JWT + CRM JWT verification; keep the existing unverified `Bearer test` path only when `ENVIRONMENT` is not production/staging. Rejected: disabling CRM manager routes.
- **Content-negotiate `/city` rather than deleting the city-runtime API.** `/city` is both a React route and `platform_orchestrator` status API. HTML navigations get the SPA; `Accept: application/json` keeps the 401/JSON contract.
- **Persistence evidence from existing `SystemHealth` rows** rather than a new heartbeat table or a destructive CRM write. Rejected: unauthenticated CRM inserts.

## Known pre-existing debt (unchanged)

- `src/web` `tsc -b` fails in unrelated Odessa/Agro/Hercules/crypto verticals (Vite production build is the blocking gate).
- Unauthenticated CRM list reads (`/customers`, `/leads`, `/automation/queue`) still return empty collections; mutations stay 401.
- `tests/test_database_stabilization_37_1.py` stale Alembic head pin; `tests/test_production_release.py` version mismatch.
- Local Mac has no Docker (`DOCKER_BUILD=UNAVAILABLE` in 13.1).
- Free Render web sleeps on idle (cold start).

## Tests

`tests/test_sprint_14_production_verification.py` plus Sprint 13/13.1 health tests and CRM Sprints 8–13 suites.

Do not start Sprint 15 or Casino work until this sprint is explicitly accepted.
