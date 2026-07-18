# SDK Certification

> Generated: 2026-07-18 13:53:32 UTC

## Verdict: **FAIL**

| Check | Status |
|-------|--------|
| SDK → Repository | FAIL |
| SDK → Database | FAIL |

## Violations

- `platform_sdk/base_vertical.py:93: imports repositories.request_repository`
- `platform_sdk/manager_provider.py:46: imports repositories.user_repository`
- `platform_sdk/manager_provider.py:48: imports repositories.manager_repository`
- `platform_sdk/base_vertical.py:100: uses get_session`
- `platform_sdk/base_vertical.py:91: imports database.models.client_request`
- `platform_sdk/base_vertical.py:92: imports database.session`
- `platform_sdk/base_vertical.py:92: uses get_session`
- `platform_sdk/manager_provider.py:47: imports database.session`
- `platform_sdk/manager_provider.py:47: uses get_session`
- `platform_sdk/manager_provider.py:50: uses get_session`

## Required Pattern

```python
# platform_sdk must call services only
from services.request_service import RequestService
await RequestService.create_request(...)
```

