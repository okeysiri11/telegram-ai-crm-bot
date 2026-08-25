# Sprint 13 — Production Host Recovery + CRM Operations Hardening + Live Deployment Verification

## Baseline

`5f80901ede221c2044eb877c06031f99a64d2e6b` on `develop` (Sprint 12 accepted, committed, pushed).
Local HEAD matched `origin/develop`. Worktree was clean. Alembic head `s8n901234567` (count 1).

## Root cause of the dead public host

The "production host" was **two Cloudflare quick tunnels started from the developer's laptop**
(`scripts/start_remote_https.py`, AUTO 1.8.5): one fronting a **Vite dev server** on :5180, one
fronting the API on :8080. Quick-tunnel hostnames are ephemeral — they die with the tunnel
process/machine. Evidence:

- last recorded URL `logos-philip-environment-determination.trycloudflare.com`
  (docs/SPRINT_MOBILE_REMOTE_RECOVERY_RESULT.md, 20 Aug 2026) now resolves **NXDOMAIN**;
- no PaaS configuration exists (no vercel/render/railway/fly/Procfile), no CI deploy job;
- the repo's durable deploy path (`docker-compose.prod.yml`: postgres + redis + bot API +
  nginx serving `src/web/dist`) targets a self-managed host for which no credentials/inventory
  exist in the repo, and nothing was running publicly.

Classification: `PROVIDER_CONFIGURATION` (ephemeral tunnel as de facto production) with `DNS`
(NXDOMAIN) as the observable symptom. Not a build, import, or migration failure — the backend
and schema were healthy once started.

## What shipped

### 1. Verified public host runner — `scripts/start_public_host.py` (new)

Production-grade replacement for the fragile two-tunnel laptop setup:

- requires the **production SPA build** (`src/web/dist`) — fails clearly if missing;
- reuses a running API on :8080 or starts API-only mode (never a second Telegram bot);
- serves SPA + API **same-origin** through the existing `scripts/serve_web_gateway.py`
  (no Vite dev server, no CORS split);
- one public HTTPS tunnel (cloudflared) to the gateway;
- refuses to report a URL until public root / assets / SPA route / `/liveness` / `/readiness`
  / CRM read / auth-gate checks all pass; failed verification exits non-zero and terminates
  children — no silent broken host;
- if the local system resolver lags/filters fresh tunnel hostnames (observed on the Cloud
  Agent VM: internal resolver NXDOMAIN while 1.1.1.1/8.8.8.8 resolve), verification falls
  back to public-DNS resolution with edge-pinned HTTP checks and logs the anomaly;
- writes the verified URL to `data/public_host.url` (gitignored).

### 2. Health/readiness identity hardening — `services/production_readiness_suite.py`

Additive only (existing keys and status codes unchanged; `services/production_readiness_test.py`
contract still holds):

- `/liveness`, `/readiness`, `/health` now include `service` (`ados-platform-api`),
  `service_version` (ConfigurationCenter `PLATFORM_VERSION`), `runtime`
  (`production`/`development`);
- `/readiness` additionally exposes a top-level `database` status field;
- no credentials, tokens, or connection URLs in any payload (asserted by tests).

Liveness remains process-alive; readiness remains dependency-validated (database/redis/api/
scheduler/telegram) with 200/503 semantics — reused, not duplicated.

### 3. CRM production operational summary (read-only)

- `ManagerIntelligenceService.operational_summary()` — deterministic composition of persisted
  CRM facts through the existing Sprint 8–12 engines: active leads/deals, won/lost, open tasks,
  overdue follow-ups, SLA at-risk/breached, escalated, critical, stale deals, weighted pipeline,
  forecast summary, top-5 priority manager actions. No new datastore, no snapshot table.
- `GET /api/auto/v1/crm/manager/operational-summary` — additive route; covered by the existing
  manager-path Bearer gate (401 unauthenticated) and `bind_crm_tenant` tenant scoping.

PostgreSQL remains the Web Auto CRM source of truth (`PostgresCRMPersistence`); no in-memory
overlay was found on the manager read path (`MemoryCRMPersistence` is test-only via
`AUTO_CRM_PERSISTENCE=memory`; `CRMMetricsService._cache` is a process snapshot refreshed from
persistence — documented compatibility surface, not a source of truth).

### 4. Documentation

- `docs/deployment.md` — new "Verified public host (tunnel mode)" section;
- this result document.

## Architectural decisions

- **Extend, don't replace:** the public-host runner composes `start_remote_https.py` helpers and
  `serve_web_gateway.py` instead of introducing a new server or hosting project. Rejected:
  creating a new PaaS project (violates "do not create random new hosting projects").
- **Same-origin production serving:** the public URL fronts the built SPA + API through one
  gateway, replacing the dev-server tunnel. Rejected: re-tunneling Vite :5180 (dev server in
  production, two hostnames, CORS surface).
- **Additive health identity, non-breaking:** `service_version` instead of repurposing the
  existing `version` key (which is the readiness-suite contract `v1`).
- **Operational summary as engine composition:** one `_snapshots` pass + existing forecast/action
  aggregation; no second CRM store, no durable forecast columns (consistent with Sprint 12).

## Verification

- Targeted: `tests/test_production_health_sprint_13.py` (5 new) +
  `tests/test_auto_marketplace_crm_manager_forecasting.py` (3 new; 15 total) — **pass**.
- Broader CRM suite (automation, communications, 360, execution, intelligence, lifecycle,
  metrics, postgres, workflow, crm-api-security, crm-engine, crm-foundation): **121 passed**.
- Security suite (`test_management_security`, `test_api_v1_freeze`, `test_admin_security`):
  **37 passed**.
- Full `pytest tests/ -q -m "not slow"`: **5702 passed, 406 failed** — the 406 failures are
  **byte-identical at the Sprint 12 baseline** (verified by running the same suite on a stashed
  tree at `5f80901e`): pre-existing debt + environment-dependent tests, zero new regressions.
- Architecture governance: `validate_legacy_migration` **pass**; `validate_architecture` grade
  80.25 FAIL and `check_no_sqlite` failures (legacy `services/*`) are **identical at baseline** —
  pre-existing, untouched by this sprint.
- Alembic: single head `s8n901234567`, `upgrade head` clean on fresh Postgres 16.
- Backend sanity: API-only import path and full bot import path (with BOT_TOKEN present) both OK.
- Frontend: **typecheck (`tsc -b`) FAILS with 43 pre-existing errors**, all in
  Odessa3D/Agro/AI-command/Hercules/crypto files — Sprint 13 touches zero frontend files.
  `npx vite build` production build **succeeds**. Reported separately and honestly; not "fixed"
  to green the report.
- **Live public verification** (from outside the server process): root 200 (SPA HTML), hashed
  asset 200, SPA route `/login` 200, `/liveness` 200 with Sprint 13 identity fields,
  `/readiness` 200 `ready=true` (database healthy; redis/scheduler degraded-optional in
  API-only mode), `GET /api/auto/v1/crm/metrics` 200,
  `GET /api/auto/v1/crm/manager/operational-summary` → 401 without Bearer / 200 with Bearer,
  served live from PostgreSQL.

## Deferred / known debt (unchanged)

- 406 pre-existing full-suite failures (includes stale `test_database_stabilization` head pin
  and `test_production_release` version mismatch categories).
- Pre-existing frontend tsc errors (Odessa3D/Agro/AI-command/Hercules/crypto).
- `validate_architecture` grade 80.25 and legacy sqlite patterns in old `services/*`.
- Quick-tunnel hostnames remain ephemeral by nature; a durable domain requires the
  `docker-compose.prod.yml` path on a real host (runbook in `docs/deployment.md`) or a named
  Cloudflare tunnel with credentials.
