# Sprint Recruiting 1.3 — Vanguard live ingestion + marketing funnel

**Date:** 2026-08-27

## What shipped

Vanguard remains a **project/source inside Recruiting**. No second vertical and no duplicate Recruiting workspace.

End-to-end cycle now exists:

`/vanguard` public career form → visitor/session + UTM tracking → `POST /api/vanguard-site/v1/applications` → `VG-XXXXXX` reference → Recruiting ingest → Vanguard project lead → qualify → candidate → INTERVIEW.

### Control center

Recruiting → Projects → Vanguard shows Overview, Traffic, Attribution, Recruiting, Marketing funnel, Campaigns, Activity, Website, Integration.

Missing metrics render **Нет данных**. CPL is shown only when campaign spend exists.

### Live ingestion

Public form generates `VG-` + 6 Crockford-style characters, then calls `submit_vanguard_application()` → `ingest_vanguard_lead()`. HMAC `POST /api/recruiting-ops/v1/vanguard/leads` remains for server-to-server. The browser never holds `VANGUARD_INGEST_SECRET`.

Preserved on the lead: name, email, country, language, unit, program, message, timestamp, UTMs, visitor/session, referrer, landing page, reference.

Duplicates: same `external_id`+vacancy or same email+non-empty program → `200 duplicate`.

### Tracking contract

Events: `page_view`, `application_open`, `application_start`, `application_submit`, `application_success`.

Forbidden: passwords, tokens, IP, user-agent, fingerprints.

### Campaigns

Domain fields + channel catalog (Google, Meta, Instagram, TikTok, Telegram, YouTube, Organic, Referral, Direct, Other). `ads_api=not_connected`. No paid ads APIs in this sprint.

### Communication loop

Note, task, qualify, convert, pipeline move, communication log. Channels PHONE/EMAIL/TELEGRAM/WHATSAPP/MANUAL. `sent` is always false; delivery is `manual_log_only`.

### Integration failure (diagnosed, not hidden)

Previous **Сбой** mixed website UNKNOWN into overall integration and/or treated Postgres `SELECT 1` as enough while `recruiting_ops_records` was missing.

Now:

- Website status and integration status are independent.
- **Проверить интеграцию** probes website HTTP (if `VANGUARD_WEBSITE_URL` set), HMAC secret, Recruiting API, and `recruiting_ops_records`.
- Returns CONNECTED / DEGRADED / DISCONNECTED with `reason_ru`.

Local verified after applying Alembic `u1q234567890`:

- Website: DISCONNECTED — `VANGUARD_WEBSITE_URL` unset
- Integration: CONNECTED — HMAC + API + table present

### Live E2E (local)

Submitted through the **same public application endpoint the `/vanguard` UI uses** (Vite `:5180` proxy → API `:8080`). No direct DB insert.

- Reference `VG-WJNV2X`
- `storage=postgres`, `durable=true`
- Visible in Vanguard leads + activity `vanguard_lead_ingested`
- Qualify → convert → INTERVIEW persisted after API re-read

Playwright was not in the repo; a headed click through the form widgets was not executed.

## Architectural decisions

- Public career site lives at `/vanguard` + `applications/vanguard_site` (project website, **not** a business vertical).
- Server-side apply so the ingest secret never ships to the browser.
- Extend `services/recruiting_ops` rather than a new platform package.
- Applied pending Alembic `t9p012345678` (chain predecessor) then `u1q234567890` so `recruiting_ops_records` exists. Casino tables from the predecessor revision were created only as required by the migration chain.

Rejected: HMAC in the browser; fabricating visits; seeding a fake lead; treating localhost as a production website URL.

## Tests

- pytest: `tests/test_sprint_vanguard_live_1_3.py` + 1.0/1.1/1.2 recruiting suites — 26 passed
- vitest: recruiting 1.0/1.2 + `src/vanguard/vanguardCareer.test.tsx` — 7 passed
- `npx vite build` (src/web) succeeded

## Not production-ready

Public apply is unauthenticated (no captcha/rate limit). Tracking `fetch` is best-effort with no retry. Ads and message-sending providers are not connected. `VANGUARD_WEBSITE_URL` is unset (local form is `/vanguard`). Browser Playwright E2E is not in CI.

## Next sprint

Paid advertising APIs (Meta/Google/TikTok) remain out of scope until requested. Next should be production hardening: public apply rate-limit/captcha, `VANGUARD_WEBSITE_URL`, ingest retry/outbox, Playwright E2E, messaging providers.
