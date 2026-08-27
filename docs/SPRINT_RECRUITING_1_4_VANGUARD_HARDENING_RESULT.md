# Sprint Recruiting 1.4 — Vanguard production hardening + real E2E gate

**Date:** 2026-08-27  
**Commit target:** `origin/develop`

Vanguard remains a **project inside Recruiting**. No new vertical and no second Vanguard project.

## What shipped

### Public apply

`POST /api/vanguard-site/v1/applications` now enforces:

- JSON payload size (`VANGUARD_APPLY_MAX_BYTES`, default 32 KiB) → 413
- normalized email validation
- `asyncio.wait_for` timeout (`VANGUARD_APPLY_TIMEOUT_SECONDS`, default 15s) → 504
- per-IP and per-email sliding-window rate limit → 429 + `Retry-After`
- `Idempotency-Key` / `idempotency_key` (same key → one lead, HTTP 200 duplicate)
- structured logs without stack traces, DB URLs, or secrets in client JSON
- stable `reference` (`VG-XXXXXX`) after successful submission

Valid applications are not silently discarded.

### Rate-limit policy

| Knob | Default |
| --- | --- |
| `VANGUARD_APPLY_RATE_LIMIT` | 20/min development, 8/min production |
| `VANGUARD_EVENTS_RATE_LIMIT` | 60/min |
| `VANGUARD_RATE_WINDOW_SECONDS` | 60 |

Limiter lives in `services/recruiting_ops/public_limits.py` (not the global 600/min API middleware). Client IP uses `X-Forwarded-For` / `X-Real-IP` when present, else the socket peer. Frontend controls are not trusted.

### Anti-bot

Provider-independent `services/recruiting_ops/antibot.py`. Reserved adapters: Turnstile, hCaptcha, reCAPTCHA.

- Development may use `VANGUARD_ANTIBOT_PROVIDER=test` + token `vanguard-test-pass`.
- Production fails closed if anti-bot is required and no real provider secret is set.
- `captcha_active` is never true unless a real provider is wired (none are wired this sprint).

### Idempotency

Retries with the same idempotency key return the same lead id and reference. After a successful browser submit, the session key is cleared so a *new* application can be created.

### Tracking

Events: `page_view`, `application_open`, `application_start`, `application_submit`, `application_success`.

- `event_id` deduplication
- client: 4 attempts, exponential backoff (`trackingRetry.ts`)
- server: persist retry (3 attempts) then `DELIVERED` / `RETRYING` / `FAILED`
- tracking failure does **not** block a valid application
- analytics are not fabricated for undelivered events

### Health (independent)

| Concept | Meaning |
| --- | --- |
| Website health | Can the configured public URL be reached? (`VANGUARD_WEBSITE_URL`) |
| Integration health | Can Vanguard securely talk to Recruiting? (HMAC + Recruiting API + database) |

States: `CONNECTED` / `DEGRADED` / `DISCONNECTED` / `UNKNOWN`. UI maps them to ONLINE / DEGRADED / OFFLINE / NO DATA.

Unknown or disconnected **website** health is not converted into an integration failure. **Проверить интеграцию** POSTs `/api/recruiting-ops/v1/projects/vanguard/integration/check`.

Diagnostics include last checked, last successful check, last application, last synchronization, and a human-readable failure reason.

### Durability

Postgres persist sets `persistence_mode=POSTGRES`. Memory fallback is labelled `NON_DURABLE_DEVELOPMENT_MODE`. Production persist/patch fail closed. Alembic head `u1q234567890` (single head).

### HMAC / replay

Unchanged contract, tests extended:

- env-only secret (`VANGUARD_INGEST_SECRET`; never `VITE_*`)
- `hmac.compare_digest`
- 300s timestamp window
- nonce replay rejected (in-process store)

Tests: valid / missing / invalid / expired / replayed.

### Advertising foundation (no live APIs)

`GET /api/recruiting-ops/v1/ads/foundation` — Meta / Google / TikTok `not_connected`, `fake_data=false`. UI: «Провайдер не подключен». Entity types reserved for next sprint.

### CI

`production-gate.yml`:

- recruiting/vanguard pytest (1.0–1.4)
- alembic single-head re-check
- scoped vitest
- `npx vite build` (blocking)
- `vanguard-e2e` Playwright job on Ubuntu (Chromium)

Local macOS 13 cannot install Playwright browsers (`Playwright does not support chromium/firefox/webkit on mac13`). That is reported as **BLOCKED**, not faked PASS.

## Architectural decisions

- Dedicated Vanguard limiter rather than lowering the global 600/min middleware.
- Anti-bot interface without shipping a commercial SDK this sprint.
- Playwright drives `/vanguard` then Owner login then Recruiting UI; slim `scripts/run_vanguard_e2e_api.py` starts the same handlers if `:8080` is free. CI uses `PYTHON=python3` because GitHub runners have no `.venv`.

Rejected: HMAC in the browser; pretending CAPTCHA is on; connecting ads/messaging APIs; substituting DB inserts or API posts for the Playwright form submit.

## Live acceptance (API, 2026-08-27)

Running local API after restart (`sprint=recruiting_1.4`):

- `REFERENCE=VG-J6PHWB`
- apply storage `postgres` / `durable=true` / `persistence_mode=POSTGRES`
- duplicate idempotency key → same lead id
- qualify → convert → INTERVIEW persisted after reload
- invalid / missing / expired HMAC → 401
- replayed nonce → 401
- apply rate limit → 429 + `Retry-After`
- website `DISCONNECTED` (URL unset) while integration `CONNECTED`

Real Playwright click-through was **not** executed on this machine (see BLOCKED reason above).

## Production readiness

`PRODUCTION_READY=NO` — the written rule requires a real browser submission on this sprint’s gate. Local Playwright browsers cannot be installed on macOS 13, and Google Chrome.app is not present. CI Ubuntu Playwright is configured but was not observed green in this session.

## Technical debt

See the completion report keys. HMAC nonces remain process-local (multi-instance replay store is not Redis-backed). No commercial CAPTCHA, ads, or messaging provider is connected.
