# Security Certification

> Generated: 2026-07-18 13:53:32 UTC

## Verdict: **FAIL**

## Authentication & Authorization

| Control | Status |
|---------|--------|
| Management API JWT/API Key | PASS (test_management_security.py) |
| Unauthorized admin routes | FAIL |
| Dedicated admin security suite | FAIL |

## Exposed Admin Routes (unauthenticated)

- `GET /api/v1/managers/pool (managers_pool_router.py)`
- `GET /api/v1/sla/overdue (sla_router.py)`
- `GET /api/v1/sla/risk (sla_router.py)`
- `GET /api/v1/sla/statistics (sla_router.py)`
- `GET /api/v1/sla/owner-escalated (sla_router.py)`
- `GET /api/v1/workflows (workflow_router.py)`
- `GET /api/v1/assignment/statistics (assignment_router.py)`
- `GET /api/v1/verticals (platform_sdk_router.py)`
- `GET /api/v1/configuration (configuration_router.py)`
- `GET /api/v1/configuration/export (configuration_router.py)`
- `POST /api/v1/configuration/validate (configuration_router.py)`
- `POST /api/v1/configuration/import (configuration_router.py)`
- `GET /api/v1/configuration/{key:.+}/history (configuration_router.py)`
- `POST /api/v1/configuration/{key:.+}/rollback (configuration_router.py)`
- `GET /api/v1/configuration/{key:.+} (configuration_router.py)`
- `PUT /api/v1/configuration/{key:.+} (configuration_router.py)`
- `DELETE /api/v1/configuration/{key:.+} (configuration_router.py)`

## Known Gaps

- Config read allows anonymous actor when `actor_telegram_id` is None
- Config write accepts `changed_by` without actor verification
- No tests asserting 401 on `/api/v1/sla/*`, `/api/v1/configuration/*`

## Security Test Evidence

- ``
- `-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html`
- `22 passed, 10 warnings in 2.54s`
