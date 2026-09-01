# Sprint Vanguard Recruiting 2.6 — make the live application visible

**Date:** 2026-09-01  
**Status:** code complete; production counters require a Render deploy of this commit

Vanguard remains a **project inside Recruiting**. HMAC ingest headers and signing were not changed. Recruiter JWT auth from Phase 2.5 was not reverted. No demo/seed leads were added.

## ROOT_CAUSE

HMAC ingest writes a real lead to `recruiting_ops_records` under the **ingest organization** (`VANGUARD_ORGANIZATION_ID` or `ados`). Recruiter GET `/api/recruiting-ops/v1/leads` (and dashboard / Vanguard project cards) scoped by `_org(request)`:

1. `X-Organization-Id` from the org selector, then
2. `X-Tenant-Id`, which `apiFetch` overwrites with the session JWT `tenantId`.

Owner demo login JWT is typically `demo-corp`. The org selector also includes Demo Corp. Ingest never writes `demo-corp`. Lists and counters therefore returned **0** while Vanguard **integration health stayed ONLINE**: health uses process-global `_ingest_log` plus an `ados` DB probe, not the recruiter read org.

A second defect: `ensure_hydrated` could mark an org hydrated after a failed DB load, leaving an empty in-memory bag after worker restart even when Postgres still had the row. Hydration now merges DB rows by id and only marks hydrated after a successful load.

The timestamp around `2026-09-01T12:59:21+00:00` on the Vanguard integration panel is `last_check_at` (opening the page / running a check), **not** proof that a lead `created_at` exists.

This environment cannot query production Postgres. If a prior website submit returned HTTP 201/200 with `durable: true`, the row committed (`get_session()` commits on success; production has no memory fallback). After deploy, owner lists should recover that row. If they stay empty, the previous application was **not** persisted and one new manual website submit is required.

## WRITE_IDENTITY

- `POST /api/recruiting-ops/v1/vanguard/leads` (HMAC, unchanged)
- `organization_id` / `tenant_id` = `canonical_vanguard_org()` (`VANGUARD_ORGANIZATION_ID` or `ados`)
- `project_key` = `vanguard` (forced)
- `source` = website value or `vanguard` (`vanguard-global` still belongs to project `vanguard`)
- table = `recruiting_ops_records`, `kind=lead`, JSONB payload

## READ_IDENTITY

- Recruiter pages send `X-Recruiting-Organization-Id` (preferred by `_org`) plus `X-Organization-Id`
- Owner + UI/JWT alias `demo-corp` / `default` / `ados` → read org `ados` on the client
- Owner GET for those aliases also hydrates ingest aliases (`ados`, `default`, canonical) on the server
- Non-owner recruiter stays on the requested org only
- Owner on an unrelated tenant (e.g. `globefly`) is **not** scanned across tenants

## Architectural decisions

- **Extend Recruiting Ops read scope** for owner + known Vanguard aliases instead of writing ingest into `demo-corp` or seeding data.
- **Do not wildcard all tenants** for owners (rejected: would leak other organizations into Recruiting home).
- **Prefer `X-Recruiting-Organization-Id`** so `apiFetch` overwriting `X-Tenant-Id` cannot hide ingest rows.
- **Keep HMAC ingest and Phase 2.5 JWT auth unchanged.**

## Production verification (after Render deploy)

Do **not** submit a new application first. Sign in as owner, open Recruiting home and Vanguard → Leads.

1. Recruiter pages must not show HTTP 401.
2. Vanguard Site / Database / Integration / Tracking remain ONLINE.
3. If the prior real application was persisted, Leads ≥ 1 on home, Vanguard Leads, applications today/7d, and last application — same row, no seed data.
4. If all counters stay 0: `PREVIOUS_APPLICATION_PERSISTED = NO`. Then submit **one** manual Vanguard website application and confirm the same counters.
