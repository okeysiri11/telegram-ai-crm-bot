# Sprint Vanguard Recruiting 3.0.2 — historical candidate merge

**Date:** 2026-09-02  
**Production:** `https://ados-web.onrender.com`

Explicit, auditable merge of duplicate candidate profiles. Leads and applications stay independent. Identity reuse is Phase 2.10 `identity_decision` (no second algorithm). Detection does not auto-merge existing rows.

ROOT_CAUSE = Historical convert created one candidate per lead. Phase 2.10 stops new splits; existing timofii QUALIFIED + APPROVED rows remained two active profiles.

MERGE_IMPLEMENTED = YES  
MERGE_ATOMIC = YES (`_persist_merge_batch` one Postgres transaction; bags updated only after persist, or unchanged on `PersistUnavailable`)  
MERGE_IDEMPOTENT = YES (second call returns `already_merged` without duplicating leads/apps/pipeline cards)

HISTORICAL_DUPLICATE_FOUND = NOT_RUN  
HISTORICAL_DUPLICATE_MERGED = NOT_RUN

LEADS_BEFORE = NOT_RUN  
LEADS_AFTER = NOT_RUN

APPLICATIONS_BEFORE = NOT_RUN  
APPLICATIONS_AFTER = NOT_RUN

ACTIVE_CANDIDATES_BEFORE = NOT_RUN  
ACTIVE_CANDIDATES_AFTER = NOT_RUN

PIPELINE_CARDS_BEFORE = NOT_RUN  
PIPELINE_CARDS_AFTER = NOT_RUN

FINAL_PIPELINE_STAGE = NOT_RUN

UTM_PRESERVED = YES (local)  
CAMPAIGN_PRESERVED = YES (local)  
EXTERNAL_ID_PRESERVED = YES (local)  
VACANCY_HISTORY_PRESERVED = YES (local)  
RECRUITER_PRESERVED = YES (local)  
NOTES_PRESERVED = YES (local)  
MERGE_AUDIT_CREATED = YES (local `candidate_merged` activity)

IDENTITY_NORMALIZATION_REGRESSION = PASS (`tests/test_sprint_recruiting_2_10_identity.py`)  
NEW_APPLICATION_DEDUP_REGRESSION = PASS (2.10 convert still links same person; merge tests include that path)  
PIPELINE_REGRESSION = PASS  
HMAC_REGRESSION = PASS (`tests/test_sprint_vanguard_hardening_1_4.py` / ingest suites)  
JWT_REGRESSION = PASS (`tests/test_sprint_recruiting_2_5_auth.py`)  
OWNER_ADOS_REGRESSION = PASS (`tests/test_sprint_recruiting_2_6_visibility.py`)

PYTEST = PASS (3.0.2 + 2.5–2.10 + 1.0/1.2/1.3/1.4/1.5/1.6/1.8/1.9/email/whatsapp/tracking)  
VITEST = PASS (3.0.2 + 2.5–2.10 + 1.0/1.2)  
VITE_BUILD = PASS (`npx vite build` in `src/web`)

COMMIT_SHA = pending push  
PUSH_STATUS = pending  
PRODUCTION_SHA = NOT_RUN  
RENDER_DEPLOYMENT = NOT_RUN

PRODUCTION_E2E = NOT_RUN  
REMAINING_BLOCKERS = Production merge of historical timofii after this SHA is live on Render.

READY_FOR_PHASE_3_1 = NO

## Architectural decisions

- One additive route: `POST /api/recruiting-ops/v1/candidates/{candidate_id}/merge`. Preview uses the same route with `preview: true`.
- Safety: `match` → recruiter may merge; `ambiguous`/`unsafe` → 409 unless owner + `force=true`; recruiter force → 403.
- Duplicate row is marked `merged` / `merged_into`, not deleted. Hidden from candidate list and pipeline.
- Frontend duplicate badge uses server `possible_duplicate` / `duplicate_candidate_ids` (normalized email AND phone). No client-side identity algorithm.

## API

```
POST /api/recruiting-ops/v1/candidates/{candidate_id}/merge
{ "duplicate_candidate_id": "...", "reason": "...", "force": false, "preview": false }
```
