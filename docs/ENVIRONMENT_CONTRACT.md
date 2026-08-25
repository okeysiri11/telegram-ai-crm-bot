# Environment contract — durable production

Durable production reads secrets from **gitignored** `.env.production`, never from the repository.

Quick-tunnel preview (`scripts/start_public_host.py`) is **not** a production environment.

## Required keys

Documented in `.env.example` and enforced by `scripts/validate_secrets_env.py`:

| Key | Production rule |
|-----|-----------------|
| `BOT_TOKEN` | Real Telegram token, or API-only mode if bot polling is disabled |
| `DATABASE_URL` | `postgresql+asyncpg://…` — PostgreSQL only |
| `POSTGRES_PASSWORD` | Must not be `CHANGE_ME`, `postgres`, `admin` |
| `REDIS_URL` | Required when `ENVIRONMENT=production` |
| `IAM_JWT_SECRET` | Required; no placeholder |
| `API_JWT_SECRET` | Required |
| `JWT_SECRET` | Required |
| `IAM_LOGIN_SECRET` | Required |
| `GRAFANA_ADMIN_PASSWORD` | Required; no placeholder |
| `OPENROUTER_API_KEY` | Optional for API-only if unused, documented |

## Injected at deploy

| Key | Source |
|-----|--------|
| `GIT_SHA` / `SOURCE_REVISION` | `git rev-parse HEAD` via `scripts/deploy_production.sh` and Dockerfile `ARG GIT_SHA` |
| `ENVIRONMENT` | `production` on the compose bot service |

## Forbidden in git

`.env`, `.env.local`, `.env.production`

## Validation

```bash
python scripts/validate_secrets_env.py
python scripts/production_doctor.py --offline
python scripts/production_doctor.py --production   # requires a real .env.production
```
