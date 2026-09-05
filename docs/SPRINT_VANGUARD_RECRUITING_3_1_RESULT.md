# Sprint Vanguard Recruiting 3.1 — pipeline E2E + TEST traffic exclusion

**Date:** 2026-09-05  
**Production:** `https://ados-web.onrender.com`

Full recruiter cycle I–R: assign → QUALIFIED → schedule interview → APPROVED → HIRED → reload → persist → history → funnel → TEST excluded from production analytics.

## 1. AUDIT FINDINGS

- Assign / qualify / convert / stage already existed (`POST /leads/{id}/assign`, `/qualify`, `/convert`, `POST /candidates/{id}/stage`).
- `pipeline_moved` activity stored only `pipeline_stage` (no `from_stage` / `to_stage`).
- Interview was a stage click only — no interview task + `interview_scheduled` audit.
- Analytics / ads funnel / source analytics counted **all** leads, including historical `utm_source=e2e_test` / `utm_campaign=vanguard_e2e` / `e2e-historical` (3.0.2 merge rows).
- Operational lists correctly kept TEST rows; production metrics did not exclude them.
- Telegram remains frozen. WhatsApp / Meta / Google stay `WAITING_PROVIDER` / `not_connected` without credentials.

## 2. FIXED

- Production analytics no longer mix TEST / e2e traffic into funnel, source, campaign, or ads overview counts.
- Pipeline history records `from_stage` → `to_stage` on every move.
- Scheduling interview creates an open «Провести интервью» task and `interview_scheduled` activity (idempotent).
- Lead workflow success copy is no longer cleared when assignee/vacancy persist (2.9 UX).

## 3. IMPLEMENTED

- `traffic_class` = `TEST` | `PRODUCTION` on create lead/candidate (UTM / `e2e_*` / explicit class).
- `production_cohort()` used by `/analytics`, ads control center, and Vanguard project marketing funnel.
- Additive routes: `POST /candidates/{id}/assign`, `POST /candidates/{id}/interview`.
- UI: TEST badge, candidate recruiter assign, «Назначить интервью», analytics excluded-count.

## 4. STILL BLOCKED BY EXTERNAL CREDENTIALS

- WhatsApp Cloud API, Meta Ads, Google Ads, Telegram (frozen by product decision).
- Vanguard website HMAC ingest remains a separate site integration (unchanged).
- Live owner JWT for a browser production I–R pass is not minted in this sprint (demo auth is disabled in production builds). Local TestClient I–R passed.

## 5. DB MIGRATIONS

None. `traffic_class` and richer activity payloads store in existing Recruiting Ops JSON `payload`.

## 6. API CHANGES

Additive only:

- `POST /api/recruiting-ops/v1/candidates/{candidate_id}/assign` `{assignee}`
- `POST /api/recruiting-ops/v1/candidates/{candidate_id}/interview`
- `GET /analytics` and ads/project marketing now include `traffic.production_only` + `excluded_test_*`
- `pipeline_moved.payload` adds `from_stage`, `to_stage` (keeps `pipeline_stage`)

No `/api/v1` or `/management/v1` contract changes.

## 7. FRONTEND CHANGES

- `RecruitingBusinessPage.tsx` — TEST suffix, interview/assign wiring, analytics copy
- `CandidateWorkflowPanel.tsx` — assign + schedule interview
- `LeadWorkflowPanel.tsx` — TEST badge; persist success stays visible
- `recruitingWorkflow.ts` — `isTestTraffic`

## 8. TESTS RUN

- pytest: `test_sprint_recruiting_3_1_pipeline.py` + 1.0 / 1.2 / 1.5 / 1.8 / 1.9 / 2.5 / 2.8 / 2.9 / 2.10 / 3.0.2 / whatsapp — **PASS**
- vitest: `sprint_recruiting_3_1_pipeline.test.tsx` + 1.0 / 2.9 / 3.0.2 — **PASS**
- `npx vite build` (`src/web`) — **PASS**

## 9. E2E RESULT

Local TestClient I–R (assign, QUALIFIED, interview, APPROVED, HIRED, reload, history pairs, funnel, TEST excluded): **PASS**

Production I–R (assign → HIRED → reload → funnel on a live owner session): **NOT_RUN**. `/management/identity/login` with email/password returns 401 (`telegram_init_data` / login_proof required). Demo auth is disabled in production builds. Do not report production persistence PASS.

Production regressions on SHA `82b5f1e3`:
- `GET /api/recruiting-ops/v1/analytics` → 401 `authentication_required`
- `POST /api/recruiting-ops/v1/vanguard/leads` unsigned → 401 `missing_signature`
- `GET /api/recruiting-ops/v1/providers` → 401 `authentication_required`
- `GET /health` Telegram `frozen=true` / `DISABLED`; ads `connected=false`; WhatsApp `NOT_CONFIGURED`

Provider honesty: no mock CONNECTED.

## 10. DEPLOYMENT STATUS

COMMIT_SHA = `82b5f1e31d7b593842df0d3e1f8b0cf32f5db7e5`  
PUSH_STATUS = PUSHED `origin/develop`  
PRODUCTION_GATE = PASS (backend-gate, web-gate, vanguard-e2e, production-foundation)  
PRODUCTION_SHA = `82b5f1e31d7b593842df0d3e1f8b0cf32f5db7e5`  
RENDER_DEPLOYMENT = YES (`GET /liveness` revision matched)

## 11. REMAINING ISSUES

- Historical production e2e leads remain in operational lists (intentional) and drop out of analytics after this SHA is live.
- Production browser I–R still needs an owner session (ISAM / real JWT).
- Ads providers remain disconnected until real credentials.

## 12. NEXT RECOMMENDED SPRINT

**3.2 — production owner-session I–R** on the live SHA: run I–R on a TEST-tagged lead, confirm Postgres reload, confirm funnel `excluded_test_*` on historical vanguard_e2e rows, keep Telegram frozen and providers waiting.

## Architectural decisions

- Extend `services/recruiting_ops/attribution.py` instead of a new `platform_*` package.
- Keep TEST rows in CRM lists; exclude only analytics / ads / project marketing.
- Interview scheduling reuses tasks + stage INTERVIEW — no calendar provider.
- Detection markers: `e2e_test`, `e2e-historical`, `vanguard_e2e`, `e2e-`, `traffic_class=TEST`.
