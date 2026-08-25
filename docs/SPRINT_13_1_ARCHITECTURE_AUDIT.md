# Architecture audit — Sprint 13.1 durable deployment

## What already existed (reuse)

| Piece | Path | Verdict |
|-------|------|---------|
| Production compose | `docker-compose.prod.yml` | Durable path. Postgres not published. Placeholder passwords remain operator-owned. |
| App image | `Dockerfile` + `docker-entrypoint.sh` | Needed HEALTHCHECK, revision, non-root user. |
| Edge | `nginx.conf` | SPA + `/api`. Missing `/liveness` `/readiness` until this sprint. |
| Secrets example | `.env.example` + `scripts/validate_secrets_env.py` | Sound. `.env.production` already gitignored. |
| CI | `.github/workflows/architecture.yml` | Ran only on `main`/`master`. `develop` was uncovered. |
| Health | `/liveness` `/readiness` `/health` via `ProductionReadinessSuite` | Sprint 13 added service identity. This sprint adds `revision`. |
| CRM | Auto Marketplace Web CRM on PostgreSQL | Sprint 7–13 engines remain SoT. Operational summary from Sprint 13 kept. |
| Backup | `scripts/backup_postgres.sh` / `restore_postgres.sh` | Reused for rollback. |
| Preview tunnel | `scripts/start_public_host.py` | Sound as **preview**. Invalid as production. |

## Gaps closed in 13.1

- Durable deploy entrypoint `scripts/deploy_production.sh` (compose, no tunnels)
- Production doctor (offline engineering gate)
- Environment contract documentation
- CI on `develop` + production-foundation job
- Health `revision` from `GIT_SHA`
- Nginx health aliases
- Explicit Quick Tunnel demotion
- Rollback wrapper that refuses silent Alembic downgrade

## External blockers (not fabricated)

No VPS inventory, DNS records, TLS certificates, or PaaS credentials exist in this repository. Engineering can be production-ready without an actual public host being live.
