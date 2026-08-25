# Deployment — Closed Beta

**Sprint:** 31.0 Closed Beta RC

## Stack

| Layer | Compose / path |
|-------|----------------|
| App API | `bot` service · Dockerfile |
| Postgres / Redis | `docker-compose.prod.yml` |
| Edge | `nginx.conf` (SPA + `/api` proxy) |
| Metrics | Prometheus + Grafana |

## Required secrets (prod)

- `POSTGRES_PASSWORD`
- `GRAFANA_ADMIN_PASSWORD`
- `IAM_JWT_SECRET` / `SECURITY_MASTER_KEY`
- `GOOGLE_CLIENT_ID` (production Google Sign-In)
- `VITE_DEMO_AUTH=false` for web build

## Deploy sequence

```bash
# 1. Build web
cd src/web && npm ci && npm run build && cd ../..

# 2. Configure .env.production (no default Grafana/Postgres passwords)

# 3. Start
docker compose -f docker-compose.prod.yml up -d --build

# 4. Health
curl -fsS http://localhost/health
```

## Verified public host (tunnel mode — Sprint 13)

When no VPS/Docker host is available, `scripts/start_public_host.py` brings up the
same production surface behind one HTTPS quick tunnel and refuses to report a URL
until public checks pass (root, assets, SPA route, `/liveness`, `/readiness`,
CRM read, auth gate). It serves the **production** `src/web/dist` build same-origin
through `scripts/serve_web_gateway.py` (never the Vite dev server) and reuses a
running API instead of starting a second bot.

```bash
npx vite build            # in src/web — production SPA build
.venv/bin/python scripts/start_public_host.py
# verified URL written to data/public_host.url (ephemeral: dies with the process)
```

See `docs/SPRINT_13_PRODUCTION_HOST_RECOVERY_RESULT.md` for the recovery record.

## TLS

Uncomment the TLS server block in `nginx.conf` and mount certs under `/etc/nginx/certs/`.

## See also

[INSTALLATION.md](./INSTALLATION.md) · [INFRASTRUCTURE_SECURITY.md](./INFRASTRUCTURE_SECURITY.md) · [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) · `docs/deployment.md`
