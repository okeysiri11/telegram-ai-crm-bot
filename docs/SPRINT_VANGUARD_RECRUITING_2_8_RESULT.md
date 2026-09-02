# Sprint Vanguard Recruiting 2.8 — Recruiting CRM operations

**Date:** 2026-09-02  
**Status:** code complete; needs Render deploy of this commit

Phases 2.5–2.7 remain in place: recruiter JWT, owner→`ados` mapping, HMAC ingest, same-origin Recruiting Ops URLs. No seed/demo leads. No new Alembic tables.

## ROOT_CAUSE / previous limitation

The Recruiting desk already stored leads, vacancies, notes, assignment, and conversion in `recruiting_ops_records` JSONB, but operator CRM actions were incomplete and conversion was not idempotent:

- Lead status could not be set to `lost` through a dedicated route; `converted` was not reserved to `/convert`.
- Vacancy update and lead→vacancy assignment had no HTTP routes.
- `convert_lead` only looked at `lead.candidate_id`. A second convert (or a concurrent pair) could create a second candidate for the same lead.
- `move_candidate` used `_find(org)` instead of `_locate`, so owner alias reads (`demo-corp` / `ados`) could miss a candidate after hydrate.

Email/phone are **not** a uniqueness key. Two independent leads with the same contact remain two leads and become two candidates.

## What shipped

- Durable lead status: `new` / `qualified` / `lost` via `POST /leads/{id}/status`. Converted only via `/convert`.
- Recruiter assignment and notes unchanged, now covered by persistence tests.
- Vacancy create + update (`POST /vacancies/{id}`) and assign vacancy to a lead (`POST /leads/{id}/vacancy`).
- Convert lock + lookup by `lead_id` / `candidate_id`. Repeat convert returns HTTP 200, same candidate, `already_converted`.
- Candidate pipeline moves use `_locate`.
- UI: hide Convert on converted leads; Lost; vacancy assign; close vacancy.

## Architectural decisions

- **Extend `services/recruiting_ops`**, do not add a new CRM package or Alembic table. Status, assignee, notes, vacancy, and pipeline already live on JSONB records.
- **Idempotency is per lead_id**, not per email/phone. Contact reuse must not collapse independent applications.
- **No HMAC / JWT / owner-mapping change.** New routes sit next to existing Recruiting Ops handlers and use the same RBAC (`observer` view-only; `hiring_manager` cannot convert).

## DB migrations

None. Production Render startup still runs `alembic upgrade head` via `scripts/run_production_web.py` (see `docs/deployment.md`). This sprint does not add a revision, so startup applies existing heads only.

## Production verification after deploy

Do not treat this file as live Render verification. After the new SHA is deployed:

1. Hard-refresh Recruiting → change a lead status, assign recruiter, add a note, assign a vacancy.
2. Convert a lead once; convert again — still one candidate.
3. Move the candidate in the pipeline and reload — stage remains.
4. Confirm no `:8080` copy and HMAC ingest still accepts signed Vanguard posts.
