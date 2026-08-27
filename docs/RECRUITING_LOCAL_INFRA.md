# Recruiting / Vanguard local infrastructure

Vanguard is a **project inside Recruiting**. This file covers Redis and the single development startup path.

## Redis (Docker Compose)

Do not install Redis with Homebrew. Use Compose:

```bash
scripts/recruiting_infra.sh start
scripts/recruiting_infra.sh health
scripts/recruiting_infra.sh logs
scripts/recruiting_infra.sh stop
```

File: `docker-compose.recruiting.yml` (Redis 7 alpine, AOF, volume `recruiting_redis_data`, healthcheck `redis-cli ping`, port 6379).

Host env:

```
REDIS_URL=redis://127.0.0.1:6379/0
VANGUARD_SHARED_STORE_URL=redis://127.0.0.1:6379/0
```

The backend detects Redis from `VANGUARD_SHARED_STORE_URL` or `REDIS_URL` (PING). `shared=true` only with a live Redis client.

- Development without Redis: `process_local`, `SHARED=NO`.
- Production without Redis: fail-closed (`unavailable`), HTTP 503 `store_unavailable`. Never silent process_local. Never `SHARED=YES` from process memory.

If Docker CLI is missing (dangling Docker.app volume), `recruiting_infra.sh` prints `BLOCKED` and does not fake health.

## Single development startup

```bash
scripts/recruiting_dev.sh
```

Starts:

1. Redis via Compose (if Docker is available)
2. API on `:8080` only if the port is free (no second backend)
3. Vite on `:5180` only if the port is free
4. Health curl against `/api/recruiting-ops/v1/health` and `/vanguard`

Tracking worker runs **in-process** with the API.

PostgreSQL is the existing local/CI database (`DATABASE_URL`). This Compose file does not start Postgres — use the already-running local Postgres or the full platform compose if you manage DB that way.

## Website URL

`VANGUARD_WEBSITE_URL` is **not** auto-filled. Unset → `NOT_CONFIGURED` (not disconnected).

Documented public SPA host (set explicitly if it is the live Vanguard site):

`https://ados-web.onrender.com/vanguard`

## Ads / messaging / anti-bot

Credentials are server-side only (`never VITE_*`). This sprint validates configuration and reports `NOT_CONFIGURED` / `CONFIGURED`. Live Meta/Google/TikTok/Telegram/WhatsApp/SMTP calls are not made. Journal communications stay `sent=false`.

## Diagnostics

Cabinet: **Рекрутинг → Инфраструктура** (`/workspace/recruiting/infra`)

API: `GET /api/recruiting-ops/v1/ops/diagnostics`
