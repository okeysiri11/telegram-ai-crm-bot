# Deployment

Production deployment guide for the Telegram CRM platform.

## Requirements

| Component | Version |
|-----------|---------|
| Python | 3.10+ (tested on 3.14) |
| PostgreSQL | 14+ |
| Redis | 6+ (optional, for FSM) |
| Docker | For local infra |

## Environment variables

Key settings in `.env` (see `.env.example`):

| Variable | Purpose |
|----------|---------|
| `BOT_TOKEN` | Telegram bot token |
| `DATABASE_URL` | PostgreSQL async URL |
| `REDIS_URL` | FSM storage (optional) |
| `DEFAULT_AUTO_MANAGER_ID` | Default auto manager Telegram ID |
| `OWNER_ID` | Platform owner Telegram ID |
| `API_HOST` / `API_PORT` | HTTP API bind (default `0.0.0.0:8080`) |
| `OPENROUTER_API_KEY` | LLM integration |

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d postgres redis
alembic upgrade head
PYTHONPATH=. python bot.py
```

## Docker Compose services

`docker-compose.yml` provides:

- **postgres** — primary database
- **redis** — FSM and caching

Bot process runs on host or in a separate container (not included in default compose).

## Startup sequence

`startup.py` runs on bot launch:

1. Register Telegram routers (modular first, legacy last)
2. Ensure permission seeds
3. Ensure auto manager provisioning
4. Start background scheduler (SLA, escalations)
5. Start HTTP API server (`api/server.py`)
6. Run startup diagnostics

## HTTP API

Default: `http://localhost:8080`

| Endpoint | Purpose |
|----------|---------|
| `/health` | Liveness |
| `/ready` | Readiness (includes DB check) |
| `/metrics` | Prometheus metrics |

## Database migrations

Always run migrations before deploying new code:

```bash
alembic upgrade head
```

Rollback strategy: keep backward-compatible migrations; avoid destructive changes without dual-write period.

## Observability

- Structured logging (`logging` module)
- Prometheus metrics in `services/observability.py`
- Sentry hook (configure via env)
- Audit log: `PlatformAuditEngineV1`

## CI checks

Recommended pipeline steps:

```bash
PYTHONPATH=. python3 scripts/check_handler_session_access.py
PYTHONPATH=. python -m pytest tests/   # when available
alembic check                          # migration consistency
```

## Production checklist

- [ ] `DATABASE_URL` points to production PostgreSQL
- [ ] `BOT_TOKEN` set and webhook/polling mode chosen
- [ ] `DEFAULT_AUTO_MANAGER_ID` configured
- [ ] Redis available for FSM (or accept memory fallback risk)
- [ ] Alembic at head
- [ ] Permission seeds applied (automatic on startup)
- [ ] API auth configured (`api/middleware.py`)
- [ ] Backups enabled for PostgreSQL

## Scaling notes

- Bot polling: single active poller per `BOT_TOKEN`
- Webhook mode: configure reverse proxy + aiogram webhook
- DB pool: `database/engine.py` — pool_size=20, max_overflow=40
- Horizontal API: stateless; scale aiohttp workers behind load balancer

See also [deployment.md](deployment.md) for legacy deployment notes.
