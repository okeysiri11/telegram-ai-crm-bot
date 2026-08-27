# Sprint Recruiting 1.5 — Advertising & Lead Acquisition Control Center

**Date:** 2026-08-27  
**Commit target:** `origin/develop`

Vanguard remains a **project inside Recruiting**. No new vertical. Live Meta/Google/TikTok APIs are **not** connected.

## What shipped

### Advertising control center

`GET /api/recruiting-ops/v1/ads/control-center` returns provider-neutral campaign metrics mapped to Recruiting project **Vanguard**.

Manual campaign CRUD:

- `POST /api/recruiting-ops/v1/campaigns`
- `POST /api/recruiting-ops/v1/campaigns/{id}`
- Operator-entered spend is REAL; provider impressions/clicks stay empty until APIs are connected (`missing_provider_metrics`, «Нет данных провайдера», `fake_data=false`).

Persisted entity kinds (same `recruiting_ops_records` JSONB table): `ad_account`, `ad_set`, `creative`, `audience`, `ads_metrics`.

### Attribution

Leads store `first_touch_*` and `last_touch_*`. Duplicate ingest updates last-touch only; first-touch is never overwritten.

### Funnel and source analytics

Marketing funnel steps (visit → interview) plus per-source leads/candidates/conversion. Cost fields: CTR, CPC, CPL, CostPerCandidate when inputs exist.

### Shared rate limit and replay stores

`services/recruiting_ops/shared_store.py`:

- Redis when `REDIS_URL` / `VANGUARD_SHARED_STORE_URL` is reachable (`shared=true`)
- otherwise `process_local` (`shared=false`), labelled honestly

HMAC nonce claim is distributed when Redis is shared. Tests inject a dict-backed store to prove multi-instance semantics.

### Tracking worker

`TrackingWorker` retries persist up to 5 times. Exhausted retries are terminal `FAILED`. No fabricated `DELIVERED`. `POST /api/recruiting-ops/v1/tracking/retries` drains the queue.

### Website health

Unset `VANGUARD_WEBSITE_URL` → `NOT_CONFIGURED` (not `DISCONNECTED`). Unreachable configured URL remains `DISCONNECTED`. Website status still does not drive integration failure.

### UI

Recruiting labels are Russian. Provider names stay **Meta Ads**, **Google Ads**, **TikTok Ads**. Campaign form lives on Vanguard → Кампании (no extra top-level nav item). Layout uses stacked grids on small screens.

### Alembic

Head `v2r345678901` (single): payload indexes on `campaign_id`, `project_key`, `event_id`.

## Architectural decisions

- Extend `recruiting_ops_records` kinds instead of a second ads database.
- Shared store interface with Redis, not a new platform package.
- Do not invent provider metrics.

Rejected: connecting live ads APIs this sprint; adding a second Recruiting nav item for advertising.

## CI browser E2E

Playwright spec still covers Vanguard form → Recruiting INTERVIEW. On this machine Playwright browsers cannot be installed (`Playwright does not support chromium/firefox/webkit on mac13`). Reported **BLOCKED**, not faked PASS. Ubuntu job `vanguard-e2e` remains in `production-gate.yml`.
