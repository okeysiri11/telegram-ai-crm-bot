# Deployment — Durable production (Sprint 13.1)

**Durable production path:** `docker-compose.prod.yml` on a persistent host with real DNS and TLS.

**Not production:** Cloudflare Quick Tunnels (`scripts/start_public_host.py`) are **PREVIEW only**. They die with the process and must never be reported as the public production URL.

## Stack

| Layer | Compose / path |
|-------|----------------|
| App API | `bot` service · Dockerfile |
| Postgres / Redis | `docker-compose.prod.yml` (Postgres is not published) |
| Edge | `nginx.conf` (SPA + `/api` + `/liveness` `/readiness` `/health`) |
| Metrics | Prometheus + Grafana |
| Identity | `GIT_SHA` / health `revision` |

## Required secrets (prod)

See [ENVIRONMENT_CONTRACT.md](./ENVIRONMENT_CONTRACT.md). Never commit `.env.production`.

- `POSTGRES_PASSWORD` (not `CHANGE_ME` / `postgres`)
- `GRAFANA_ADMIN_PASSWORD`
- `IAM_JWT_SECRET` / `SECURITY_MASTER_KEY`
- `GOOGLE_CLIENT_ID` (production Google Sign-In)
- `VITE_DEMO_AUTH=false` for web build

## Deploy sequence

```bash
# 1. Build web
cd src/web && npm ci && npm run build && cd ../..

# 2. Configure .env.production (no default Grafana/Postgres passwords)

# 3. Doctor + deploy (durable compose — no tunnels)
python scripts/production_doctor.py --offline
./scripts/deploy_production.sh

# 4. Health
curl -fsS http://localhost/liveness
curl -fsS http://localhost/health
```

## Preview host (tunnel mode — not production)

`scripts/start_public_host.py` can front a **production SPA build** for a short-lived demo. The hostname is ephemeral. Use it only as a preview. Durable production remains compose + DNS + TLS.

```bash
npx vite build            # in src/web — production SPA build
.venv/bin/python scripts/start_public_host.py
# preview URL written to data/public_host.url (ephemeral: dies with the process)
```

See `docs/SPRINT_13_PRODUCTION_HOST_RECOVERY_RESULT.md` for the Sprint 13 recovery record.

## Rollback

```bash
./scripts/backup_postgres.sh
./scripts/rollback_production.sh --restore-backup backups/ados_pg_*.dump
# Alembic downgrade is never automatic.
```

See [PRODUCTION_ROLLBACK.md](./PRODUCTION_ROLLBACK.md).

## TLS

Uncomment the TLS server block in `nginx.conf` and mount certs under `/etc/nginx/certs/`.

## See also

[INSTALLATION.md](./INSTALLATION.md) · [INFRASTRUCTURE_SECURITY.md](./INFRASTRUCTURE_SECURITY.md) · [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) · [ENVIRONMENT_CONTRACT.md](./ENVIRONMENT_CONTRACT.md)
