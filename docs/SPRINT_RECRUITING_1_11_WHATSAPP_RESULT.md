# Sprint — Recruiting WhatsApp production (1.11)

**Date:** 2026-08-27  
**Branch:** `origin/develop`  
**Backend:** `recruiting_1.11`

Productionize real WhatsApp Cloud API for Recruiting. Telegram stays intentionally frozen. Meta/Google/TikTok Ads are not connected.

## What shipped

- Live health: Graph `GET /{phone_number_id}` (never sends a message)
- Human-confirmed outbound send; AI draft is advisory-only
- Provider HTTP accept ≠ delivered; delivery/read/failed come from webhooks
- Inbound webhook + candidate phone matching + unresolved senders
- HMAC `X-Hub-Signature-256` when App Secret is set; duplicate suppression
- Templates list (`GET /{waba}/message_templates`)
- Retry via existing `provider_http`; rate limit via existing `public_limits`
- Metrics on existing `services.observability` (no second stack)
- Conversation UI: badge WhatsApp, incoming/outgoing, statuses, Написать / Ответить / Создать с AI / Отправить
- Docs: `docs/recruiting/WHATSAPP_PROVIDER_SETUP.md`

## Architectural decisions

- Extend `services/recruiting_ops/` (`whatsapp_ops.py` + existing SecretStore / provider_http / observability). No new monitoring or Redis stack.
- Telegram freeze overlay is unchanged; adapter HTTP for Telegram is not developed.
- Ads adapters are untouched.
- Injected HTTP in tests is `mocked_http=true`, `live_verified=false` — not production evidence.

## Intentionally deferred

Automatic owner test message. Telegram unfreeze. Meta/Google/TikTok live connect. Native template-send campaign blasts.

## Green gate

- Scoped backend pytest (1.0, 1.5, 1.6, 1.8, 1.9, tracking recovery, email SMTP, WhatsApp): **108 passed**
- Scoped frontend vitest (1.0–1.9 recruiting + email SMTP + WhatsApp): **34 passed**
- Production `npx vite build`: **passed**
- REAL_WHATSAPP_HEALTH=NOT_RUN (WhatsApp env names absent locally)
- WHATSAPP_STATUS=NOT_CONFIGURED
- TELEGRAM=FROZEN_DISABLED

## Real connection gate

Inspected process env **names only**. WhatsApp credentials are absent: `REAL_WHATSAPP_HEALTH=NOT_RUN`, `WHATSAPP_STATUS=NOT_CONFIGURED` is a valid sprint result. Do not invent credentials. A real test message requires explicit owner action after CONNECTED.
