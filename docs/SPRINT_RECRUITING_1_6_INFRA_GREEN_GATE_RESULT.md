# Sprint Recruiting 1.6 — Infrastructure green gate + provider readiness

**Date:** 2026-08-27  
**Commit target:** `origin/develop`

Vanguard remains a **project inside Recruiting**. No new vertical. Live Meta/Google/TikTok accounts are **not** connected. PASS is never faked.

## What shipped

### Redis local infrastructure

`docker-compose.recruiting.yml` — Redis 7 only (healthcheck, AOF, named volume). Scripts:

- `scripts/recruiting_infra.sh start|stop|health|logs`
- `scripts/recruiting_dev.sh` — Redis + existing API `:8080` + Vite `:5180` without duplicating listeners

Backend auto-detects Redis from `REDIS_URL` / `VANGUARD_SHARED_STORE_URL`. Production has **no** silent process_local fallback.

### Shared rate limit and HMAC replay

`services/recruiting_ops/shared_store.py`:

- Redis Lua sliding window (atomic ZADD/ZCARD)
- Nonce `SET NX EX`
- `shared=True` only with a live Redis client
- Production miss/unreachable → `backend=unavailable`, `fail_closed=True`, HTTP 503 `store_unavailable` (not `bad_signature`)

### Tracking health

Durable Postgres rows with FAILED/RETRYING are **reclassified** to DELIVERED (`recovery_reason=persisted_in_postgres`). Events are not deleted.

Classes: `delivered`, `retry_scheduled`, `delivery_failed`, `provider_not_configured`.

Unconfigured ads/messaging destinations do not poison core `TRACKING_HEALTH`. Diagnostics: delivered / retrying / failed / provider_not_configured / oldest_pending / last_delivery.

`POST /api/recruiting-ops/v1/tracking/recover`

### Provider readiness

Ads, Telegram/WhatsApp/Email, Turnstile/hCaptcha/reCAPTCHA: `NOT_CONFIGURED` | `CONFIGURED` | `CONNECTED` | `DEGRADED` | `ERROR`.

No live API calls → never fake `CONNECTED`. Missing lists are non-secret field names. Tokens/secrets are redacted. Journal communications remain `sent=false`.

### Vanguard website

Unset `VANGUARD_WEBSITE_URL` → `NOT_CONFIGURED` (not DISCONNECTED). Documented example only: `https://ados-web.onrender.com/vanguard`. Not auto-wired.

### Operations diagnostics

`GET /api/recruiting-ops/v1/ops/diagnostics`  
UI: Рекрутинг → **Инфраструктура** (`/workspace/recruiting/infra`)

Russian chips: Работает / Не настроено / Ограничено / Ошибка. `NOT_CONFIGURED` is never ERROR.

### GitHub CI

`vanguard-e2e` remains Ubuntu + Chromium + Postgres + Alembic + Vite + Playwright. Redis service added to `backend-gate` and `vanguard-e2e`. Pytest 1.6 is part of the recruiting gate.

Local macOS Playwright (darwin 13, no Chrome) is **not** converted into CI PASS.

## Architectural decisions

- Slim recruiting Compose (Redis only) rather than starting the full ADOS stack.
- `SHARED=YES` strictly Redis-backed; in-process memory is never reported shared.
- Tracking recovery reclassifies durable core rows; it does not delete FAILED events.
- Provider readiness is configuration validation only — next sprint connects real APIs.

## Intentionally deferred

Real Meta/Google/TikTok connections, WhatsApp/Telegram/SMTP delivery confirmation, commercial CAPTCHA verify, AI campaign optimization.
