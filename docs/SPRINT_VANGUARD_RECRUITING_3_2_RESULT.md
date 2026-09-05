# Sprint Vanguard Recruiting 3.2 — production E2E + pre-ads gate

**Date:** 2026-09-05  
**Production:** `https://ados-web.onrender.com`

No auth bypass was added. HMAC was not weakened. Provider APIs were not mocked as connected.

## A. Live production SHA

`GET /liveness` revision during the live cycle: `d7a56414e8c26b089c55d0c45b449418b401f7b4`  
(includes Recruiting 3.1 `82b5f1e3`). Recruiting health `production=true`, `memory_fallback_allowed=false`. Workspace `/workspace/recruiting` returns the SPA (HTTP 200). Authenticated `GET /leads` / `/analytics` hydrate from Postgres.

Follow-up commit `5e57afcb` (pre-ads UTM marker + TEST/PROD column) is on `origin/develop`. Production Gate `backend-gate` failed on an unrelated OAuth callback flake (`OAuth state недействителен`) and had not reached Render at E2E time.

## B. Auth status

Owner session obtained through the **already-deployed** `POST /api/enterprise-demo-auth/v1/login` (owner role `owner` / `platform_admin`, tenant `demo-corp` → ados Recruiting read/write).  
Not added in this sprint. JWT was not hardcoded or printed.

`/management/identity/login` email/password still 401 (`telegram_init_data` / `login_proof`).  
Production frontend does not show local «Login as owner». A human already signed in can finish a browser hard-reload check (steps below).

## C–F. Vanguard ingest + UTM + candidate

Unsigned `POST /api/recruiting-ops/v1/vanguard/leads` → **401 `missing_signature`**.

Real website path:

`POST https://vanguard-global.net/api/applications` → Vercel HMAC → Render ingest → **HTTP 200** `success=true`, `duplicate=false`.

Created lead `476430f9-5b20-4eed-9cd8-2a35ae189753`, `traffic_class=TEST`, `source=vanguard-global`.

| Field | Persisted |
|---|---|
| utm_source | instagram |
| utm_medium | paid_social |
| utm_campaign | vanguard_pre_ads_test |
| utm_content | creative_test_01 |
| landing_page | `https://vanguard-global.net/apply?utm_source=instagram&…` |
| referrer | `https://www.instagram.com/` |

Candidate `1d85e804-0ca1-4377-bf06-4d008de62bfd` created on convert. `durable=true`, `storage=postgres`. One application, one `lead_id`.

## G–J. Lifecycle, reload, history

Same TEST row, authenticated production API (then GET reload):

| Step | Result | Actor | Timestamp (UTC) |
|---|---|---|---|
| ingest / lead_created | NEW | platform_owner | 07:53:20 |
| assign `recruiter.ira` | persisted | platform_owner | 07:53:22 |
| qualify | `qualified` | platform_owner | 07:53:22 |
| convert | QUALIFIED | platform_owner | 07:53:22 |
| schedule interview | INTERVIEW + `interview_scheduled` | platform_owner | 07:53:23 |
| APPROVED | APPROVED | platform_owner | 07:53:23 |
| HIRED | HIRED | platform_owner | 07:53:23 |

Reload `GET /candidates` + `GET /leads`: still **HIRED**, assignee `recruiter.ira`, UTM intact, `traffic_class=TEST`.

History pairs: `QUALIFIED→INTERVIEW`, `INTERVIEW→APPROVED`, `APPROVED→HIRED`. Actions also include `vanguard_lead_ingested`, `lead_assigned`, `lead_qualified`, `lead_converted`, `interview_scheduled`.

Browser Cmd+Shift+R was not run in this agent (no owner UI session). API reload after Postgres persist **did** run.

## K. TEST exclusion

| Metric | Before | After |
|---|---|---|
| Production funnel leads / qualified / hired | 0 / 0 / 0 | 0 / 0 / 0 |
| `excluded_test_leads` | 7 | 8 |
| `excluded_test_candidates` | 4 | 5 |
| CRM lead list | 7 | 8 |
| CRM candidate list | 3 | 4 |
| Ads overview leads | — | 0 |
| Ads `source_analytics` | — | empty (no instagram) |
| Ads `fake_data` | — | false |
| Ads spend / CPL / CPA | — | unavailable (no live ads) |

All 8 operational leads are TEST-tagged (historical e2e + this pre-ads row). None enter production funnel.

`5e57afcb` adds `vanguard_pre_ads_test` as an explicit marker and a TEST/PROD column. Until that SHA is live, this row is TEST via `external_id` / `e2e-` (3.1). Do not auto-delete historical e2e rows.

## L. Remaining blockers

- Meta / Google / WhatsApp credentials (honest NOT_CONFIGURED / WAITING_PROVIDER).
- Telegram frozen.
- Browser hard-reload still needs the owner’s existing UI session.
- `5e57afcb` not on Render until Production Gate is green.

## M. Pre-Ads readiness: **READY** (ingest → CRM hire). Ads APIs **BLOCKED**.

| Component | Status |
|---|---|
| Tracked Vanguard URL + UTM | READY (this run) |
| Landing / apply page | READY |
| HMAC signed ingest | READY |
| Unsigned rejected | READY |
| CRM Lead | READY |
| Candidate + application | READY |
| Recruiter assign | READY |
| Qualify | READY |
| Interview schedule + history | READY |
| Decision APPROVED / HIRED | READY |
| Postgres persist + reload | READY |
| TEST excluded from production/ads metrics | READY |
| Meta Ads API | BLOCKED |
| Google Ads API | BLOCKED |
| WhatsApp | BLOCKED |
| Telegram | BLOCKED (frozen) |
| Browser hard reload | NOT TESTED (API reload PASS) |

### Provider honesty

- Telegram: `frozen=true`, `DISABLED`
- WhatsApp: `NOT_CONFIGURED`, tracking `WAITING_PROVIDER`
- Meta / Google: ads `not_connected`; cards `NOT_CONFIGURED` / `WAITING_PROVIDER`
- No mock CONNECTED

## Human browser hard-reload (if already logged in as owner)

1. Open `https://ados-web.onrender.com/workspace/recruiting?view=candidates`
2. Search `TEST` or `Pre Ads Test`
3. Open the HIRED card — recruiter Ira, campaign `vanguard_pre_ads_test`
4. Open Activity — QUALIFIED → INTERVIEW → APPROVED → HIRED
5. Hard reload (Cmd+Shift+R / Ctrl+Shift+R)
6. Confirm the same HIRED card, recruiter, UTM, and history
7. Open Analytics — production hired stays 0; TEST excluded count includes this row

Do not submit a second live application unless it is also TEST-tagged.

## Architectural decisions

- Live apply used the real Vercel signing path, not a local HMAC secret.
- TEST isolation used existing 3.1 `e2e-` / `traffic_class` rules; `vanguard_pre_ads_test` marker is additive.
- Historical e2e rows were identified, not deleted.
