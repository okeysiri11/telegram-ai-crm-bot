# Sprint Vanguard Recruiting 3.0.2 — historical candidate merge

**Date:** 2026-09-02  
**Production:** `https://ados-web.onrender.com`

ROOT_CAUSE = Convert created one candidate per lead. Phase 2.10 stopped new splits; historical timofii still had two active profiles (APPROVED + QUALIFIED) plus a third linked application from 3.0.1.

MERGE_IMPLEMENTED = YES  
MERGE_ATOMIC = YES  
MERGE_IDEMPOTENT = YES

HISTORICAL_DUPLICATE_FOUND = YES  
HISTORICAL_DUPLICATE_MERGED = YES

Inspected on production SHA `5ee0530570e721ea2123ee8a4b8a6134d9cbfa12` before merge (lookup by email, IDs not hardcoded in product code):

| Record | ID | Stage / status | Recruiter | Notes |
|---|---|---|---|---|
| Candidate (canonical) | `a69decf0-2854-4802-b9a3-326804a90fc0` | APPROVED | recruiter.owner | 2 lead_ids, vacancy дронщик on later app |
| Candidate (duplicate) | `32394cd8-616d-42c9-a088-e16f25c3adda` | QUALIFIED | recruiter.owner | 1 lead_id |
| Lead | `5c0d8019-af02-4e6d-906b-db38727d88fa` | converted → canonical | recruiter.owner | source vanguard-global, UTM e2e_test / vanguard_e2e, external_id `7054694b-…` |
| Lead | `5d43c412-758b-40bc-b2f0-50ff147fab98` | converted → canonical | recruiter.owner | vacancy дронщик, UTM e2e-historical, external_id `e2e-timofii-d88c3ef1` |
| Lead | `033290ad-593e-4dd7-b1c5-bcc5c52bc61a` | converted → duplicate | recruiter.owner | UTM e2e_test / vanguard_e2e, external_id `50f17fb2-…` |

Pipeline before: 2 cards (QUALIFIED + APPROVED). Identity safety: **match** (same normalized email + phone). Merge via `POST /api/recruiting-ops/v1/candidates/{canonical}/merge` with `force=false`.

LEADS_BEFORE = 3  
LEADS_AFTER = 3

APPLICATIONS_BEFORE = 3 leads / 2+1 snapshots  
APPLICATIONS_AFTER = 3 leads linked; candidate `applications` length 2 (QUALIFIED row only stored a `{lead_id}` stub; all three leads remain). UI application count uses `lead_ids` → 3.

ACTIVE_CANDIDATES_BEFORE = 2  
ACTIVE_CANDIDATES_AFTER = 1

PIPELINE_CARDS_BEFORE = 2  
PIPELINE_CARDS_AFTER = 1

FINAL_PIPELINE_STAGE = APPROVED

UTM_PRESERVED = YES (leads still have `e2e_test` / `e2e-historical` / `vanguard_e2e`)  
CAMPAIGN_PRESERVED = YES (`utm_campaign=vanguard_e2e` on original leads)  
EXTERNAL_ID_PRESERVED = YES (`7054694b-…`, `e2e-timofii-d88c3ef1`, `50f17fb2-…`)  
VACANCY_HISTORY_PRESERVED = YES (дронщик / vacancy_id `192b4af9-…` on lead `5d43c412-…`)  
RECRUITER_PRESERVED = YES (`recruiter.owner`)  
NOTES_PRESERVED = YES (no notes were present; none deleted)  
MERGE_AUDIT_CREATED = YES (`candidate_merged`, activity id `bbbae7b9-656a-4beb-9e00-9d3335b7af77`, durable postgres)

IDENTITY_NORMALIZATION_REGRESSION = PASS  
NEW_APPLICATION_DEDUP_REGRESSION = PASS (Test C: two converts, one candidate, two leads, two applications)  
PIPELINE_REGRESSION = PASS  
HMAC_REGRESSION = PASS (unsigned ingest → 401 `missing_signature`)  
JWT_REGRESSION = PASS (candidates without bearer → 401 `authentication_required`)  
OWNER_ADOS_REGRESSION = PASS (owner JWT `demo-corp` read `ados` Vanguard rows)

PYTEST = PASS (3.0.2 + 2.5–2.10 + 1.0/1.2/1.3/1.4/1.5/1.6/1.8/1.9/email/whatsapp/tracking locally; CI Production Gate recruiting suite green on `5ee05305`)  
VITEST = PASS (3.0.2 + 2.5–2.10 + 1.0/1.2 locally; CI scoped vitest green)  
VITE_BUILD = PASS (`npx vite build` in `src/web`)

COMMIT_SHA = `7c4f7b1bd74c6dae76622ae57dcbc670d8a6f4f0`  
PUSH_STATUS = PUSHED `origin/develop`  
PRODUCTION_SHA = `7c4f7b1bd74c6dae76622ae57dcbc670d8a6f4f0`  
RENDER_DEPLOYMENT = YES (`GET /liveness` revision matched)

Historical merge + Tests A/B/C were executed on `5ee0530570e721ea2123ee8a4b8a6134d9cbfa12` (then live). After the snapshot-link follow-up deployed as `7c4f7b1b`, production was re-checked: still 1 active candidate, 3 leads, 1 APPROVED pipeline card, idempotent rematch `already_merged`, HMAC unsigned 401, JWT missing 401.

PRODUCTION_E2E = PASS  
- Test A historical timofii merge on this SHA: ACTIVE_CANDIDATES=1, LEADS_PRESERVED=PASS, APPLICATIONS_PRESERVED=PASS (3 leads kept), PIPELINE_CARD_COUNT=1, PIPELINE_STAGE=APPROVED, RECRUITER/VACANCY/UTM/EXTERNAL_ID/NOTES/MERGE_AUDIT=PASS  
- Test B second merge: `already_merged=true`, still 1 candidate / 3 leads / 1 pipeline card, no duplicate applications  
- Test C new person: PERSON_COUNT=1, LEAD_COUNT=2, APPLICATION_COUNT=2, PIPELINE_CARD_COUNT=1  

REMAINING_BLOCKERS = none for recruiter daily use of merge + 2.10 identity. Follow-up: merge now copies `_with_application_links` so stub snapshots for every `lead_id` are included (historical row already merged; leads were not dropped).

READY_FOR_PHASE_3_1 = YES

## Architectural decisions

- One additive route: `POST /api/recruiting-ops/v1/candidates/{candidate_id}/merge`. Preview uses the same route with `preview: true`. No extra endpoints.
- Safety reuses Phase 2.10 `identity_decision`: `match` → recruiter may merge; `ambiguous`/`unsafe` → 409 unless owner + `force=true`; recruiter force → 403.
- Duplicate row is marked `merged` / `merged_into` / `MERGED`, not deleted. Hidden from candidate list and pipeline.
- Frontend «Возможный дубль» uses server `possible_duplicate` / `duplicate_candidate_ids` (normalized email AND phone). No client-side identity algorithm.
- Detection never auto-merges existing production rows.

## API

```
POST /api/recruiting-ops/v1/candidates/{candidate_id}/merge
{ "duplicate_candidate_id": "...", "reason": "...", "force": false, "preview": false }
```
