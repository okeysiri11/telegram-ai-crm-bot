# Sprint Vanguard Recruiting 3.3 Phase 1 — Advertising Control Center

**Date:** 2026-09-05  
**Baseline:** Sprint 3.2 FULL PRODUCTION E2E PASS (`9cf96cc8`)

No provider credentials were invented. Meta / Google / TikTok remain disconnected. WhatsApp remains NOT_CONFIGURED. Telegram remains frozen. HMAC ingest was not changed.

## Architecture discovered (extended, not replaced)

Existing stack reused:

- `GET /api/recruiting-ops/v1/ads/control-center`
- `POST/GET /campaigns`, `recruiting_ops_records` kind `campaign` (JSONB)
- `services/recruiting_ops/ads_control.py` (`campaign_costs`)
- `services/recruiting_ops/attribution.py` (`production_cohort`, UTM first/last touch)
- `/workspace/recruiting/ads` + `AdsControlCenterPage`
- Recruiting nav «Реклама»

No new ads database. New kind `campaign_spend` lives in the same JSONB table. No Alembic migration.

## What shipped

### Backend

- Internal campaign fields: source catalog, country, program, full UTM, planned budget, origin `INTERNAL`
- `POST /campaigns/{id}/spend` — operator manual spend with audit (`manual_spend_recorded`)
- `GET /campaigns/{id}` — funnel, recruiter attribution, spend history, date window
- Control-center KPIs, `source_economics`, `provider_connect`, `date_range`
- Overview spend uses operator entries only (not fake provider spend). Impressions/clicks stay null until LIVE

### Frontend

- Title **РЕКЛАМА VANGUARD**
- KPI cards + date filters
- Campaign table + create form + detail funnel + manual spend
- Source economics table
- Provider connect placeholders that explain missing credentials
- Vanguard tab/link **Реклама** → `/workspace/recruiting/ads`

### Economics

`CTR = clicks/impressions`, `CPC = spend/clicks`, `CPL = spend/applications`, `Cost per hire = spend/hired`. Missing or zero denominator → `null` / «Нет данных» / «Нет живых данных». Never divide by zero. Never invent impressions/clicks.

### TEST isolation

`production_cohort()` still strips `traffic_class=TEST` and E2E markers from KPIs, campaign funnel, and source economics. Operational CRM lists unchanged.

### Security

Campaign create/spend require `create`/`edit`. Observer forbidden. Tenant isolation: org B cannot spend on org A’s campaign. HMAC ingest untouched.

## Tests

- `tests/test_sprint_recruiting_3_3_ads.py`
- `src/web/workspace/recruiting/sprint_recruiting_3_3_ads.test.tsx`
- Existing Recruiting suites remain in Production Gate

## Remaining blockers

Paid ads APIs (Meta / Google / TikTok), WhatsApp, Telegram — still not connected.

## Phase 2 proposal

Live provider OAuth only after real credentials; sync impressions/clicks as LIVE; never backfill invented history; campaign write approvals for pause/budget; visit tracking if website events exist.
