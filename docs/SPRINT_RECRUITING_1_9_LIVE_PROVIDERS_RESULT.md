# Sprint — Recruiting live providers (OAuth, health, metrics, messaging)

**Date:** 2026-08-27  
**Branch:** `origin/develop`  
**Backend:** `recruiting_1.9`

Move Recruiting from provider-ready to **live-provider-ready**. CONNECTED is allowed only after a successful provider API request. Missing credentials stay NOT_CONFIGURED. The 1.7/1.8 Green Gate is not reopened.

## Discovery

Local `.env` has no Meta/Google/TikTok/Telegram/WhatsApp/SMTP secrets (only `VANGUARD_WEBSITE_URL` among related keys). Render public origin: `https://ados-web.onrender.com`.

## What shipped

- Central provider registry
- Real HTTP adapters: Meta Graph, Google Ads search, TikTok Marketing, Telegram `getMe`/`sendMessage`, WhatsApp Cloud, SMTP EHLO/STARTTLS/send
- OAuth start/callback with HMAC state (Meta, Google, TikTok)
- Normalized connection test API (no secrets)
- Provider health monitor independent of core infra
- Metrics sync + campaign read sync (null, not fake zero)
- Live campaign writes and outbound messages require human approval
- AI remains advisory
- WhatsApp webhook verify + inbound statuses (no invented events)
- UI: Подключить, LIVE/MOCK/Не настроено, data sources, approvals
- `docs/recruiting/LIVE_PROVIDER_SETUP.md`

No new Alembic revision. JSONB kinds added: `campaign_write`, `outbound_message`.

## Architectural decisions

- Extend `services/recruiting_ops/` rather than a new platform package.
- Injected HTTP in tests is `mocked_http=true` and `live_verified=false` — it does not prove production connectivity.
- `providers.*.status == not_connected` on ads foundation remains for 1.5; live overlay lives in `overview.data_source`.

## Intentionally deferred

Production KMS. Real Google Ads mutate. Autonomous spend. LLM-generated recommendations. SendGrid/Mailgun/SES native APIs (SMTP envelope is the boundary).
