# Sprint 13.1 — Durable production deployment and CI foundation

## Baseline

Reconciled `develop` to `origin/develop` first (`8d0a65c9968180e6bf1fbddd3b4d896440dde419`, Sprint 13 public-host recovery). Fast-forward only. No history rewrite.

Sprint 13 Quick Tunnel work is **kept as preview** and explicitly demoted. It is not production.

## What shipped

- Architecture audit of the existing compose/nginx/health/CI/CRM stack
- Production image: HEALTHCHECK, `GIT_SHA`, non-root `ados` user
- Production compose: revision injection, tunnel demotion comment, postgres remains unpublished
- Environment contract + `GIT_SHA` in `.env.example`
- CI on `develop` plus a production-foundation job
- `scripts/deploy_production.sh` (compose only; no tunnels)
- `scripts/production_doctor.py` offline gate
- `scripts/crm_production_smoke.py`
- `scripts/rollback_production.sh` wrapping existing Postgres backup/restore
- Health `revision` identity (additive)
- Nginx `/liveness` `/readiness` `/ready`
- Quick Tunnel banner/docs: PREVIEW, not production

No second CRM store. No Alembic migration. Sprint 7–13 CRM routes unchanged except additive health identity.

## Actual deployment

No durable host credentials exist in the repository. This sprint is **engineering-ready**, not a live public cutover.

`PUBLIC_PRODUCTION_URL` is empty on purpose. A Quick Tunnel URL is not recorded as production.

## Tests

`tests/test_sprint_13_1_durable_deployment.py` plus Sprint 13 health tests and Sprint 7–12 CRM gates.
