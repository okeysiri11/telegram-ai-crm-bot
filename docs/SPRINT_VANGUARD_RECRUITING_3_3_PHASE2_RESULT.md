# Sprint Vanguard Recruiting 3.3 Phase 2 — Advertising Provider Connection Layer

**Date:** 2026-09-05  
**Baseline:** Phase 1 HUMAN E2E PASS (`b43cdf30`)

No live Meta / Google / TikTok credentials were supplied. Production must remain
`NOT_CONFIGURED` / `WAITING_PROVIDER`. MOCKED tests are labelled. MOCKED PASS ≠ LIVE CONNECTION PASS.

WhatsApp and Telegram were not connected. No live campaign writes were added.

## Architectural decisions

- **Extend, do not replace** Sprint 1.8–1.9 provider stack (`provider_oauth`, `provider_adapters`,
  `provider_live`, `secret_store`, `provider_connections`, `ads_control_center`).
- New kinds `provider_mapping` and `provider_sync_run` live in existing `recruiting_ops_records` JSONB.
- Ads credential mutations require Owner / `admin`. Messaging (WhatsApp / Email / Telegram) keeps `update`.
- `CONNECTED` is stored only after `live_verified` or explicit MOCK / injected HTTP (non-production tests).
- FX rates are not invented. Spend origins do not stack (`PREFER_PROVIDER` vs `MANUAL_ONLY`).

## What shipped

- Canonical ads states + public connection fields (tokens never returned)
- Tenant-scoped secret envelope + purge on disconnect
- OAuth nonce replay rejection; Google OAuth blocked without developer token
- Account list / select / verify; sync refuses `NOT_CONFIGURED`
- Campaign mapping UNMAPPED / SUGGESTED / MAPPED / CONFLICT
- Attribution quality + spend-origin policy on control center
- Ads → Провайдеры wizard UI with disabled-reason actions
- Diagnostics in Russian without secrets

## Tests

- `tests/test_sprint_recruiting_3_3_phase2_providers.py` (MOCKED HTTP labelled)
- `src/web/workspace/recruiting/sprint_recruiting_3_3_phase2.test.tsx`
- Regression: 1.8 / 1.9 / 3.3 ads / WhatsApp

## Remaining blockers

Real Meta / Google / TikTok app credentials and a successful live verify.
WhatsApp remains outside this sprint. Campaign writes remain approval-only and unimplemented for live mutation.
