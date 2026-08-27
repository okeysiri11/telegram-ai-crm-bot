# Sprint — Recruiting Email SMTP (1.10)

**Date:** 2026-08-27  
**Branch:** `origin/develop`  
**Backend:** `recruiting_1.10`

Productionize Email SMTP for Recruiting. Telegram stays intentionally frozen. Meta/Google/TikTok/WhatsApp are not connected in this sprint.

## What shipped

- SMTP health (EHLO/login only) and explicit test-email action
- Candidate composer: templates, preview, send, history
- SENT = SMTP accepted; never implied DELIVERED
- Retry (max 3), rate limit via existing `public_limits`, idempotency, suppression
- Header-injection / invalid recipient / safe placeholders
- Metrics on existing `services.observability` (no second stack)
- Telegram product overlay: `DISABLED` / frozen, no connect CTA, no retry storm
- Docs: `docs/recruiting/EMAIL_SMTP_PROVIDER_SETUP.md`

## Architectural decisions

- Extend `services/recruiting_ops/` (especially `email_smtp.py` + existing SecretStore / observability). No new monitoring package.
- Telegram freeze is a service/UI overlay; adapter HTTP is not rewritten.
- Ads adapters are untouched.

## Intentionally deferred

SendGrid/Mailgun/SES native APIs. Telegram unfreeze. Meta/Google/TikTok/WhatsApp live connect. Automatic mail on health check.

## Green gate

- Scoped backend pytest (1.0, 1.5, 1.6, 1.8, 1.9, tracking recovery, email SMTP): **94 passed**
- Scoped frontend vitest (1.0–1.9 recruiting + email SMTP): **passed** (email SMTP 11, plus 1.8/1.9)
- Production `npx vite build`: **passed**
- REAL_SMTP_HEALTH=NOT_RUN (SMTP env names absent locally)
- EMAIL_STATUS=NOT_CONFIGURED
- TELEGRAM=FROZEN
