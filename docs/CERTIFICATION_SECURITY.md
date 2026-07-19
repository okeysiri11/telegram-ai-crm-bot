# Security Certification

> Generated: 2026-07-19 13:07:17 UTC

## Verdict: **PASS**

## Authentication & Authorization

| Control | Status |
|---------|--------|
| Management API JWT/API Key | PASS (test_management_security.py) |
| Unauthorized admin routes | PASS |
| Dedicated admin security suite | PASS |

## Exposed Admin Routes (unauthenticated)


## Known Gaps

- Config read allows anonymous actor when `actor_telegram_id` is None
- Config write accepts `changed_by` without actor verification
- No tests asserting 401 on `/api/v1/sla/*`, `/api/v1/configuration/*`

## Security Test Evidence

- `/Users/macbook/Desktop/TelegramBotCourse/.venv/lib/python3.14/site-packages/_pytest/unraisableexception.py:33: RuntimeWarning: coroutine 'Connection._cancel' was never awaited`
- `  gc.collect()`
- `RuntimeWarning: Enable tracemalloc to get the object allocation traceback`
