# Architecture Certification

> Generated: 2026-07-18 13:53:32 UTC

## Verdict

**FAIL**

## Gate Results

| Check | Status | Detail |
|-------|--------|--------|
| Repository → Service imports | FAIL | 19 Repository → Service import(s) |
| API → Repository direct access | PASS | 0 API → Repository direct import(s) |
| Architecture audit (strict) | PASS | governance=PASS score=99.5 strict=99.5 |

## Evidence — Repository → Service

- `repositories/partner_repository.py:7: from services.partner_engine import PartnerEngine`
- `repositories/partner_repository.py:12: from services.partner_engine import PartnerEngine`
- `repositories/partner_repository.py:17: from services.partner_engine import PartnerEngine`
- `repositories/partner_repository.py:22: from services.partner_engine import PartnerEngine`
- `repositories/partner_repository.py:27: from services.partner_engine import PartnerEngine`
- `repositories/event_bus_repository.py:25: from services.event_bus_config import MAX_RETRIES, compute_backoff_seconds`
- `repositories/calendar_repository.py:7: from services.calendar_service import CalendarService`
- `repositories/calendar_repository.py:12: from services.calendar_service import CalendarService`
- `repositories/calendar_repository.py:17: from services.calendar_service import CalendarService`
- `repositories/calendar_repository.py:22: from services.calendar_service import CalendarService`
- `repositories/vin_repository.py:12: from services.vin_decoder import decode_vin, validate_vin`
- `repositories/finance_repository.py:7: from services.finance_core import FinanceCoreService`
- `repositories/finance_repository.py:12: from services.finance_core import FinanceCoreService`
- `repositories/finance_repository.py:17: from services.finance_core import FinanceCoreService`
- `repositories/finance_repository.py:24: from services.finance_core import FinanceCoreService`
- `repositories/task_repository.py:7: from services.tasks import TaskService`
- `repositories/task_repository.py:12: from services.tasks import TaskService`
- `repositories/task_repository.py:22: from services.tasks import TaskService`
- `repositories/task_repository.py:27: from services.tasks import TaskService`

## Evidence — API → Repository


## Architecture Diagram (Target)

```
API (/management/v1) → Services → Repositories → Database
SDK → Services (never Repository/Database)
Plugins → platform_plugin_sdk only
```

## Scores

- Governance score: 99.5
- Strict certification score: 34.29

