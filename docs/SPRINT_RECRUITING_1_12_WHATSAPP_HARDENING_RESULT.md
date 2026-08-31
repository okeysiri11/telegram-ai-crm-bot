# Sprint — Recruiting WhatsApp pre-live hardening (1.12)

**Date:** 2026-08-31  
**Backend:** `recruiting_1.12`

Finish WhatsApp production-readiness that does **not** require live Meta credentials. No Graph calls to Meta. No Render secret changes. No vanguard-global connection.

## What shipped

- Canonical env names: `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_BUSINESS_ACCOUNT_ID`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`. Alias `WHATSAPP_TOKEN` still accepted.
- Health `whatsapp.env_status`: `NOT_CONFIGURED` | `PARTIALLY_CONFIGURED` | `READY_FOR_LIVE_CHECK` (booleans only; no secret values).
- Template send on the existing Cloud API adapter (`type: template`, name + language + components/parameters). No hard-coded production template.
- 24-hour customer-service window: text only inside the window; otherwise `TEMPLATE_REQUIRED` with a machine-readable reason. Last inbound/outbound timestamps persisted on the candidate.
- Outbound idempotency via `Idempotency-Key` / `idempotency_key` on existing `idempotency` records. Same key does not create a second Meta send after SENT. FAILED may retry the same outbound.
- Persistent `phone_number_id` → organization (`kind=whatsapp_phone_map`), reloaded after process cache reset.
- Webhook: unknown `phone_number_id`, malformed payload, duplicate protection after successful persist, structured logs without secrets.

## Architectural decisions

- Extend `services/recruiting_ops/whatsapp_ops.py` and the existing WhatsApp adapter. No second provider.
- Reuse `recruiting_ops_records` (JSONB kinds) for phone maps, messages, and idempotency. No new table.
- Env readiness is separate from Graph `CONNECTED`. `READY_FOR_LIVE_CHECK` is not live evidence.

## Intentionally deferred

Live Meta credentials, webhook subscription, real Graph health, vanguard-global ingest, Meta/Google Ads, Recruiting UI redesign, Casino.

## Verify

Targeted pytest `tests/test_sprint_recruiting_whatsapp.py` (mocked HTTP only). Frontend vitest `sprint_recruiting_whatsapp.test.tsx` unchanged in behavior.
