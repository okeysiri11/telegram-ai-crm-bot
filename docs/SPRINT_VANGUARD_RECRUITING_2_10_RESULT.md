# Sprint Vanguard Recruiting 2.10 — candidate identity without collapsing leads

**Date:** 2026-09-02  
**Status:** code complete; needs Render deploy of this commit

Leads remain independent applications. Conversion matches a person by normalized email + phone and **links** the lead onto an existing candidate. HMAC ingest, JWT, owner→`ados`, and 2.5–2.9 routes are unchanged.

## ROOT_CAUSE

Convert created one candidate per lead. Two real applications from the same person (same email and phone) became two pipeline cards. Identity belongs on the **candidate**, not by deleting or merging lead rows.

## DEDUPLICATION_RULES

- Match only when email and phone both agree (after normalization), or one identifier is present and the other is empty.
- Same email + different phones, or same phone + different emails → **ambiguous, no merge**.
- Name is never an identity key.
- Phone formatting (`+372 810 93104` vs `37281093104`) uses existing `normalize_phone` / `phones_match`.

## MERGE_SAFETY

Leads are never deleted. Each application snapshot keeps UTM, campaign, `external_id`, and reference. Candidate first-touch is preserved; last-touch updates. Repeat convert of the same lead stays idempotent.

## DB migrations

None — `lead_ids` and `applications` are JSON fields on existing candidate records.
