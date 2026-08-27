# Sprint — Recruiting final green gate: tracking recovery

**Date:** 2026-08-27  
**Branch:** `develop`  
**Backend:** `recruiting_1.7`

No new Recruiting product features. No advertising-provider connections. Historical tracking rows were not deleted, truncated, hidden, or force-marked successful without evidence.

## Diagnosis (read-only)

Table: `recruiting_ops_records` `kind='tracking'`, organization `ados`. Delivery state lives in JSONB `payload`.

The previous report’s ~238 figure was an earlier hydrate snapshot. The actual historical backlog at recovery time was **270** rows, all already stored in PostgreSQL:

| Field | Observed |
|---|---|
| Destination | `recruiting_db` or empty core (not Meta/Google/TikTok/Telegram/WhatsApp/Email) |
| Event types | `application_submit`, `application_success`, `page_view` |
| Payload status | `RETRYING` / empty / a few `DELIVERED` |
| Attempts / last_error | unset |
| Durable evidence | the Postgres row itself |

**Root cause:** `_persist` inserted rows, then in-memory status became `DELIVERED`, but the JSONB payload was left as `RETRYING`. Hydrate reloaded `RETRYING`, health classified them as a delivery failure, and the worker queue was empty (pending=0). These events were already in `recruiting_db` and were not waiting on unconfigured ads APIs.

### Classification of the 270 historical records

```
DELIVERABLE_NOW=270
WAITING_FOR_PROVIDER=0
OBSOLETE_BUT_AUDIT_REQUIRED=0
CORRUPT=0
OTHER=0
```

Totals equal 270. Evidence for `DELIVERED` is the existing Postgres row (`recovery_reason=persisted_in_postgres` after migration).

## What shipped

- Explicit lifecycle: `PENDING`, `PROCESSING`, `RETRYING`, `WAITING_PROVIDER`, `DELIVERED`, `DEAD_LETTER` (`FAILED` is a read alias of `DEAD_LETTER`).
- Core persist success writes `DELIVERED` + durable flags into JSONB (not only memory).
- Intentionally unconfigured provider destinations land in `WAITING_PROVIDER` (HTTP 201), stay durable, and re-enter retry when `provider_is_configured` becomes true. They do not busy-loop as `RETRYING`.
- Worker: max 5 attempts, exponential backoff (`next_attempt_at`, `last_error`), terminal `DEAD_LETTER`. No live ads API calls.
- Historical migration via `migration_patch()` — never deletes.
- Health `CONNECTED` means worker + database operational, no stuck overdue `RETRYING` storm. `WAITING_PROVIDER` is counted separately and does not mark infrastructure broken. `dead_letter` is always exposed.
- Auto-migrate on live hydrate; skipped under pytest so the suite does not rewrite production rows as a side effect.

## Migration before/after

| | Count |
|---|---|
| Historical rows (affected set) | 270 |
| After recovery (`recovery_reason=persisted_in_postgres`) | 270 still present, status `DELIVERED` |
| Current table total | 368 (361 `DELIVERED` + 7 `WAITING_PROVIDER`) |
| Deleted | 0 |

The extra rows after 270 are later real ingest/test events (core `DELIVERED`, Meta `WAITING_PROVIDER`), not fabricated green status.

## Live verification

- Stopped `recruiting_1.6` PID 94887. Current listener: `scripts/run_api_local.py` PID 43579, `recruiting_1.7`, single process on `127.0.0.1:8080`.
- Redis `recruiting-redis` PONG. Rate-limit/replay backend=redis `shared=true`. Cross-instance pytest PASS.
- Postgres CONNECTED. Alembic `v2r345678901` single head.
- Controlled core event `7dc55d3b-fadb-4e37-b93c-a101935bc0c3`: HTTP 201, `DELIVERED`, `durable=true`, `storage=postgres`, row present.
- Unconfigured Meta event `e64614f3-ea22-4290-8a1e-81cc21230e04`: HTTP 201, `WAITING_PROVIDER`, row present. After restart, worker `waiting_provider` matches persisted count; `retrying=0`.
- 20s observation: no retry storm (`retrying` stayed 0, no worker persist-fail loop).

## Architectural decisions

- Keep lifecycle in JSONB on `recruiting_ops_records`; no new table, Alembic head unchanged.
- Treat an existing core Postgres row as delivery evidence for `recruiting_db` (not as an ads-provider success).
- Do not map `WAITING_PROVIDER` or `NOT_CONFIGURED` providers to tracking `DEGRADED` / UI «Ошибка».
- Skip auto-migration under `PYTEST_CURRENT_TEST`; live API still migrates on hydrate.

## Intentionally deferred

Real Meta/Google/TikTok connections, Telegram/WhatsApp/Email send, CAPTCHA, AI campaign optimization.

## Verification

- Recruiting/Vanguard pytest: 73 passed; Redis cross-instance + tracking recovery 13 passed on re-run.
- Scoped vitest: 6 files, 11 passed.
- `npx vite build`: PASS.
- asyncpg `Event loop is closed`: absent.
- Browser E2E was not faked locally; GitHub `vanguard-e2e` observed after push.
