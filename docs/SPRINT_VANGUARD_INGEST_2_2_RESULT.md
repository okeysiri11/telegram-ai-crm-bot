# Sprint Vanguard ingest 2.2 — complete external application ingest contract

**Date:** 2026-08-31  
**Status:** ingest persistence complete; production E2E not claimed

Vanguard remains a **project inside Recruiting** (`project_key=vanguard`). No Recruiting rebuild, no database redesign, no Casino changes, no live ingest secret, no deploy.

## What shipped

HMAC ingest `POST /api/recruiting-ops/v1/vanguard/leads` now persists the fields sent by vanguard-global:

- Candidate: `age`, `contact_consent`, normalized `phone` (plus already supported name/email/country/language/program/unit/message)
- Attribution: `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `gclid`, `fbclid`, `click_id` as **separate** JSONB keys
- `source` and `project_key` (`vanguard-global` / `vanguard`)

Values live in existing `recruiting_ops_records` JSONB payloads. No Alembic revision and no destructive migration. Historical records without the new keys continue to load.

## Architectural decisions

- **Extend ingest, do not replace it.** Parsers live in `services/recruiting_ops/ingest_fields.py`; HMAC headers and `{timestamp}.{nonce}.{raw_body}` are unchanged in `ingest_auth.py`.
- **Age:** optional integer 18–99. Present-but-invalid → `400 validation`. Omitted → `null`.
- **contact_consent:** exact boolean; omitted stays `null`; **never defaulted to true**.
- **Phone:** stored via the same `normalize_phone` used by WhatsApp matching so candidate-phone matching is not broken.
- **Click ids:** `gclid` / `fbclid` / `click_id` are not collapsed into one field on this HMAC path.
- **Duplicates:** existing `external_id` + vacancy policy; missing new fields may be filled on retry without creating a second lead.
- **CRM:** GET `/leads` and GET `/candidates` return the JSONB item as-is. Existing lead/candidate tables show phone, age, consent, full UTM, and click ids.

## Not done (intentionally)

- Live `VANGUARD_INGEST_SECRET`
- Production ingest / deploy
- Changes to the separate vanguard-global repo
- WhatsApp credentials, Meta Ads, Google Ads

## Tests

- `tests/test_sprint_vanguard_ingest_2_2.py` — persistence, HMAC, idempotency, legacy load, Recruiting API
- `tests/test_sprint_vanguard_ingest_1_1.py` — existing HMAC ingest
- `tests/test_sprint_recruiting_whatsapp.py` — candidate-phone matching regression
