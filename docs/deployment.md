# Deployment Guide

## Prerequisites

- Docker + Docker Compose
- Telegram bot token
- PostgreSQL 16 / Redis 7 (or use compose services)

## Quick start (prod compose)

```bash
cp .env.production .env.production.local
# edit secrets: BOT_TOKEN, DATABASE_URL, JWT_SECRET, OWNER_ID, managers

docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
.venv/bin/alembic upgrade head
```

Local development:

```bash
docker compose up -d postgres redis
.venv/bin/alembic upgrade head
PYTHONPATH=. .venv/bin/python bot.py
```

## Migrations

```bash
.venv/bin/alembic upgrade head
.venv/bin/alembic current
```

Relevant revisions:

- `f9s901234567` — client_requests, marketplace_listings
- `f9t012345678` — audit_log, inventory, lead_sla_records

## Backup

```bash
chmod +x scripts/backup_db.sh
./scripts/backup_db.sh
```

Schedule via cron (daily 03:00):

```
0 3 * * * cd /opt/TelegramBotCourse && ./scripts/backup_db.sh >> /var/log/crm-backup.log 2>&1
```

Retention: 14 days (override with `RETENTION_DAYS`).

## Nginx

`nginx.conf` proxies:

- `/api/` → bot:8080
- `/metrics` → Prometheus scrape target
- `/swagger` → OpenAPI UI

TLS termination can be added with Let's Encrypt certificates mounted into nginx.

## Observability

| Component | URL |
|-----------|-----|
| Prometheus | http://host:9090 |
| Grafana | http://host:3000 |
| Bot metrics | http://host:8080/metrics |
| Sentry | set `SENTRY_DSN` |

## Media storage switch

```env
MEDIA_STORAGE_PROVIDER=telegram   # or local | s3
MEDIA_LOCAL_CACHE=true
S3_BUCKET=
S3_ENDPOINT_URL=
MEDIA_CDN_BASE_URL=https://cdn.example.com/
```

## Health checks

- `GET /health`
- `GET /liveness`
- `GET /readiness`
- `GET /system/db-health`
