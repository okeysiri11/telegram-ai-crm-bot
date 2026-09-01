# Sprint Vanguard ingest 2.4 — production persistence + CRM visibility

**Date:** 2026-08-31  
**Status:** code and automated tests complete; one manual recruiter check remains

Vanguard remains a **project inside Recruiting**. HMAC headers and signing were not changed.

## What shipped

- Website-style ingest (no `vacancy_id`) is idempotent on `external_id` / `idempotency_key`.
- A new submission id still creates a new lead even if email and program match.
- `idempotency_key` is stored on the lead and copied onto the candidate.
- `source=vanguard-global` is treated as project `vanguard` for GET `?project=vanguard`.
- Recruiter lead/candidate details panel shows name, phone, email, age, country, language, program/unit, motivation, source/UTM/clicks, consent, created time, reference.

## Production inspection

This environment cannot read production Postgres or authenticated Recruiting GET `/leads`. No extra live application was submitted. Vercel 200 + Render ingest traffic was already confirmed in Phase 2.3.

Manual recruiter check after deploy of this Recruiting change: open `/workspace/recruiting` and `/workspace/recruiting/projects/vanguard` and confirm the existing production application card.

## Tests

`tests/test_sprint_vanguard_ingest_2_4.py` plus existing ingest 1.1 / 2.2 / projects / WhatsApp regressions.
