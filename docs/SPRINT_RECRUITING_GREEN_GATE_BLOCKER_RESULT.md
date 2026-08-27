# Sprint — Recruiting green-gate blocker removal

**Date:** 2026-08-27  
**Branch:** `develop`

No new Recruiting product features. Goal: remove remaining infrastructure blockers and report a truthful green gate.

## What shipped

### Docker CLI repair (user PATH, no sudo)

`/usr/local/bin/docker` remains a dangling root symlink to `/Volumes/Docker 1/Docker.app/...` (volume not mounted). A valid Docker Desktop 4.47.0 already exists at `~/Desktop/Docker.app`.

User-level repair: `~/.local/bin/docker` → Desktop app CLI. `scripts/recruiting_infra.sh` prefers that binary and skips the dangling `/usr/local/bin/docker`. Daemon started; Compose v2.39.4.

Do not delete the system symlink without an operator decision. Do not Homebrew-install Redis.

### Redis shared stores (proven, not mocked)

`docker compose -f docker-compose.recruiting.yml up -d` → `recruiting-redis` PONG. Backend restarted with `REDIS_URL=redis://127.0.0.1:6379/0`.

Cross-instance pytest (two Redis clients): instance A rate-limit fills the window for B; nonce claimed on A is rejected on B; TTL expiry allows reclaim. `shared=true` only with a live Redis client.

### Stale backend

PID 45359 (`recruiting_1.4`) was terminated. Current `scripts/run_api_local.py` listens on `127.0.0.1:8080` as **recruiting_1.6**. Single listener.

### Vanguard public URL

`https://ados-web.onrender.com/vanguard` is the Render `ados-web` SPA route (not a doc-only guess). It was observed HTTP 200 after a cold start earlier this session; a later 90s GET timed out (free-tier sleep). Configured locally via `.env` (not committed) and in `render.yaml` as a public non-secret. Unset remains `NOT_CONFIGURED` in tests.

### CI browser E2E

`vanguard-e2e` is self-contained on `ubuntu-latest`: Postgres + Redis services, wait via `scripts/ci_wait_tcp.py` **before** alembic, sequential API-then-Vite stack (`scripts/run_vanguard_e2e_stack.sh`), Playwright Chromium `--with-deps`, failure artifacts. `reuseExistingServer` is false in CI.

### asyncpg warning

Pytest uses `NullPool` when `PYTEST_CURRENT_TEST` is set and disposes the engine after each test (`shutdown_db`). Warning is not globally filtered. Recruiting pytest: no `Event loop is closed`.

## Architectural decisions

- Repair Docker via user PATH + existing Desktop app; do not replace the root symlink automatically.
- Keep slim recruiting Redis Compose; do not start a second container runtime.
- Configure the proven public Vanguard URL in `render.yaml` (deploy-time), not by committing `.env`.
- Extract CI port-wait into `scripts/ci_wait_tcp.py` so workflow YAML cannot break Python indentation.

## Intentionally deferred

Real Meta/Google/TikTok connections, WhatsApp/Telegram/SMTP delivery, commercial CAPTCHA, AI campaign optimization. Tracking classifier still marks non-durable `RETRYING` recruiting_db rows as DEGRADED (leftover local events; worker queue is empty).

## Verification

- Recruiting/Vanguard pytest: 50 passed (includes live Redis cross-instance).
- Scoped vitest: 10 passed.
- `npx vite build`: PASS (`tsc -b` remains report-only in CI for unrelated verticals).
- asyncpg `Event loop is closed`: absent.
