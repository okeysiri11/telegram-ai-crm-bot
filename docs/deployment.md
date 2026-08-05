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

## TLS

Uncomment the TLS server block in `nginx.conf` and mount certs under `/etc/nginx/certs/`.

## See also

[INSTALLATION.md](./INSTALLATION.md) · [INFRASTRUCTURE_SECURITY.md](./INFRASTRUCTURE_SECURITY.md) · [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) · `docs/deployment.md`
