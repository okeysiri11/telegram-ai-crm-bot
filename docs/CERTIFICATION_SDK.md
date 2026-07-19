# SDK Certification

> Generated: 2026-07-19 13:07:17 UTC

## Verdict: **PASS**

| Check | Status |
|-------|--------|
| SDK → Repository | PASS |
| SDK → Database | PASS |

## Violations


## Required Pattern

```python
# platform_sdk must call services only
from services.request_service import RequestService
await RequestService.create_request(...)
```

