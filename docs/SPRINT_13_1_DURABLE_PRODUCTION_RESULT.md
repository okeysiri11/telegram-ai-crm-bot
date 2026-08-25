# Sprint 13.1 — Durable Production Deployment + CI/CD + Permanent Host Verification

## Baseline

`8d0a65c9968180e6bf1fbddd3b4d896440dde419` on `develop` (Sprint 13 accepted, committed, pushed).
Local HEAD matched `origin/develop`. Worktree clean. Alembic head `s8n901234567` (count 1).

## Problem

Sprint 13's verified public host was a Cloudflare **quick tunnel** — ephemeral by design
(dies with the Cloud Agent VM / laptop). `DEPLOY_TRIGGER=manual`; `git push` deployed nothing.
Not acceptable as production hosting.

## Discovery

- **No provider credentials exist** in the Cloud Agent environment (no Vercel/Render/Railway/
  Fly/Cloudflare tokens; only read-scoped GitHub auth). No authenticated durable deploy path
  is available to the agent.
- Existing deployment config: `docker-compose.prod.yml` (self-managed VPS path, no host),
  `Dockerfile` (Telegram bot image). Existing CI (`architecture.yml`) triggers only on
  `main/master` — `develop` pushes were ungated.
- The API server already serves the SPA same-origin (`api/web_static.py`, `ADOS_SERVE_WEB`),
  so a durable deployment needs exactly one web service + managed Postgres (+ Redis, required
  by production config policy).

## Selected architecture (and why)

**Render Blueprint** (`render.yaml`): one Docker web service (`Dockerfile.web` →
`scripts/run_production_web.py`) + managed PostgreSQL + managed Key Value (Redis).

- infrastructure-as-code lives in the repo; **zero deployment secrets in git**
  (Render `generateValue` + dashboard-only `BOT_TOKEN`);
- git-driven deploys from `develop` gated by GitHub checks (`autoDeployTrigger: checksPass`);
- health-gated rollout: traffic switches only after `/liveness` passes → a failed build/test/
  start never replaces a healthy deployment; one-click rollback;
- stable `https://<service>.onrender.com` URL — independent of laptop, Cloud Agent VM, and
  quick tunnels;
- runs the REAL application: full API, production SPA build, PostgreSQL source of truth,
  startup migrations. No mocks, no SQLite, no static-only fake.

Rejected: creating ad-hoc PaaS projects from the agent (no credentials, and the sprint forbids
fabricating hosting); GitHub Actions-hosted runtime (not a persistent host).

## What shipped

| Piece | File(s) |
|-------|---------|
| Production web entrypoint (fail-loudly config validation, fatal-in-production migrations, SPA presence check, scheduler + CRM worker startup, provider `PORT` binding, graceful SIGTERM) | `scripts/run_production_web.py` |
| Production web image (multi-stage: Node 22 SPA build → Python 3.12 runtime) | `Dockerfile.web`, `.dockerignore` |
| Durable host blueprint (web + Postgres + Redis, checksPass deploys, `/liveness` health check) | `render.yaml` |
| CI gate on `develop` (migrations single-head gate, Sprint 13/13.1 health tests, CRM Sprints 8–13 suites, security suite, entrypoint import sanity, frontend production build; typecheck report-only) | `.github/workflows/production-gate.yml` |
| External production verification (scheduled/manual; root/assets/SPA/liveness/readiness/CRM/auth-gate + revision match; enabled by `PRODUCTION_URL` repo variable) | `.github/workflows/production-verify.yml` |
| Provider `postgresql://` → `postgresql+asyncpg://` normalization (engine + migrations) | `platform_configuration/configuration_center.py`, `migrations/env.py` |
| Web service profile readiness: `ADOS_TELEGRAM_REQUIRED=false` (explicit, manifest-recorded; production bot default unchanged) | `services/production_readiness_suite.py` |
| Deployed `revision` in `/liveness`·`/readiness`·`/health` identity (GIT_REVISION → RENDER_GIT_COMMIT fallback) | `services/production_readiness_suite.py` |
| Docs | `docs/deployment.md`, this file |

## Architectural decisions

- **Explicit service profiles over silent fallbacks:** a missing `BOT_TOKEN` in production
  stays fatal for readiness *unless* the deployment manifest explicitly sets
  `ADOS_TELEGRAM_REQUIRED=false`. Rejected: auto-detecting "web mode" (silent behavior change).
- **URL normalization at the configuration boundary** (plus a mirrored local copy in
  `migrations/env.py`, which must not import the configuration stack). Rejected: requiring
  owners to hand-edit provider connection strings.
- **checksPass instead of deploy-hook secrets:** the deploy trigger needs no GitHub secret at
  all; the gate workflow is the only check on `develop`, so a red gate blocks deploys.
  External verification runs in a *separate* workflow because a same-commit check that waits
  for the deployment would deadlock the checksPass trigger.
- **`npx vite build` in image/CI as the blocking build; `tsc -b` reported non-blocking:**
  43 pre-existing typecheck errors in unrelated verticals (Odessa3D/Agro/AI-command/Hercules/
  crypto) predate Sprint 13; both results are reported honestly (Sprint 13 record).

## Verification

- **Production simulation (this VM, `ENVIRONMENT=production`, provider-style
  `postgresql://` URL, real Redis):** config fail-fast verified (missing
  `SECURITY_MASTER_KEY` aborts startup with the exact errors); the simulation also caught and
  fixed a real deployment blocker (alembic loading psycopg2 for plain-scheme URLs). Final run:
  migrations applied, readiness **healthy / ready=true, zero degraded** (redis + scheduler
  healthy, telegram skipped by explicit profile), `/liveness` exposes
  `revision=8d0a65c9…`, SPA root/login 200, CRM read 200, auth gate 401, graceful SIGINT
  shutdown, port released.
- Targeted + security: Sprint 13/13.1 health tests (9), manager forecasting (10 + Sprint 13
  additions), management/api-freeze/admin security — **56 passed**.
- Full `pytest -m "not slow"`: see final report — compared against the Sprint 13 baseline
  failure list to prove zero new regressions.
- YAML validity: `render.yaml`, both workflows parse cleanly.

## Deployment status — honest

Repository-side preparation is **complete and validated**. The Cloud Agent has **no Render
(or any provider) credentials**, so the blueprint could not be applied from here:

- `DURABLE_DEPLOYMENT_BLOCKED=YES`
- **Minimum owner action:** Render dashboard → *New +* → *Blueprint* → connect
  `okeysiri11/telegram-ai-crm-bot` → *Apply* (render.yaml is detected automatically).
  Optionally afterwards: set `BOT_TOKEN` in the service environment, and set the GitHub
  repository variable `PRODUCTION_URL` to the service URL to activate scheduled external
  verification.

No ephemeral tunnel is described as durable production anywhere in this sprint.
