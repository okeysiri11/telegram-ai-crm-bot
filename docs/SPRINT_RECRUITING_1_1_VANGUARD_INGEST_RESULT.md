# Sprint Recruiting 1.1 — Vanguard signed ingest + production fail-closed storage

**Date:** 2026-08-27

## What shipped

- `POST /api/recruiting-ops/v1/vanguard/leads` — server-to-server HMAC-SHA256 ingest
- Secret: `VANGUARD_INGEST_SECRET` (server env only; documented in `.env.example`; never `VITE_*`)
- Production: ingest never returns success if PostgreSQL persist failed (`503 storage_unavailable`)
- DEV: memory fallback remains for operator desk / local tests and is labeled `storage=memory`
- Duplicate policy: same `external_id` + same vacancy → handled (`200`, `duplicate=true`); different vacancy → new lead
- UTM, vacancy, `external_id` stored; activity `vanguard_lead_ingested` / `lead_created`
- Recruiting cabinet lead table shows vacancy, UTM, external_id

## Architectural decisions

- **Extend Recruiting 1.0** (`/api/recruiting-ops/v1`) instead of a new `platform_recruiting` or frozen `/api/v1/leads`.
- **HMAC over the raw body** (`{timestamp}.{nonce}.{raw_body}`), 300s replay window, nonce replay rejected.
- **Fail-closed in production:** `ENVIRONMENT`/`ADOS_ENV` in `{production,prod,staging}` disables memory fallback for ingest. DEV keeps memory so local tests and operator desk still work without Postgres.
- **No new Alembic revision:** attribution fields live in existing `recruiting_ops_records` JSONB payload.
- **Website is out of this repo:** inbound is ready; connecting the actual Vanguard form is a follow-up.

## Not in this repo

The Vanguard marketing website is not in this workspace. The form is not connected here. Real browser E2E through that form was not executed.

## Tests

Targeted pytest `tests/test_sprint_vanguard_ingest_1_1.py` + `tests/test_sprint_recruiting_1_0.py` (17 passed). Vitest recruiting cabinet (3 passed). `npx vite build` for `src/web` succeeded.

## Next sprint

RECRUITING MARKETING FUNNEL + CAMPAIGN OPERATIONS
