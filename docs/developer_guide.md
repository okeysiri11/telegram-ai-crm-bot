# Developer Guide

Guide for contributing to the Telegram CRM platform under the stabilized architecture.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d postgres redis
alembic upgrade head
PYTHONPATH=. python bot.py
```

## Project layout

```
routers/                    Telegram routers (prefer for new flows)
*_handlers.py               Feature handlers
services/                   Business engines (pg_*_engine.py)
repositories/               SQLAlchemy data access
database/models/            ORM models
src/
  verticals/                Vertical registry + service facades
  platform/layers/          BaseRepository, BaseService, session policy
  domains/                  Strangler domain scaffolds
migrations/versions/        Alembic
docs/                       Architecture documentation
scripts/                    Validation helpers
```

## Architecture rules

### 1. Handlers are thin

Handlers parse Telegram/HTTP input and call services. No database access.

```python
# Good
summary = await AutoClientRequestEngineV1.get_request_summary(number)
text = ManagerDeliveryEngineV1.format_auto_client_request_card(summary)

# Bad — forbidden
async with get_session() as session:
    row = await session.execute(select(...))
```

### 2. Services own business logic

Add methods to `services/pg_<feature>_engine.py` or vertical services in `src/verticals/`.

Services open sessions, call repositories, trigger notifications and events.

### 3. Repositories are query-only

Extend `BaseRepository`, accept `AsyncSession` in constructor, implement CRUD.

No validation, no Telegram calls, no cross-entity orchestration.

### 4. Use vertical services for cross-cutting entry

```python
from src.verticals.auto.service import AutoVerticalService

await AutoVerticalService.record_vin_intake(vin=vin, car_id=car_id, created_by=user_id)
```

### 5. Do not extend legacy monoliths

- Avoid adding to `handlers.py`
- Avoid adding to `database_legacy.py`
- Register new routers in `startup.py` before legacy handlers

## Adding a feature

1. **Model** — `database/models/<feature>.py` + Alembic migration
2. **Repository** — `repositories/<feature>_repository.py`
3. **Service** — `services/pg_<feature>_engine.py`
4. **Handler** — `routers/<feature>_router.py` or `<feature>_handlers.py`
5. **Register** — add to `startup.py`
6. **Test** — `tests/` or `services/<feature>_test.py`

## Session policy check

```bash
PYTHONPATH=. python3 scripts/check_handler_session_access.py
```

Must pass before merging handler changes.

## Dependency injection

Optional via `container.py`:

```python
from container import get_container

crm = get_container().get("services.client_request_crm")
auto = get_container().vertical("auto")
```

Not wired into startup yet — direct imports remain valid.

## Permissions

See [ROLES_AND_PERMISSIONS.md](ROLES_AND_PERMISSIONS.md).

Adding permission:

1. `PLATFORM_PERMISSIONS` in `pg_platform_permissions_engine.py`
2. `ROLE_PERMISSION_MAP`
3. Restart bot

## Audit events

```python
from services.pg_platform_audit_engine import PlatformAuditEngineV1

await PlatformAuditEngineV1.log(
    event_type="STATUS_CHANGED",
    entity_type="client_request",
    entity_id=request_number,
    user_id=telegram_id,
    payload={"status": "IN_PROGRESS"},
)
```

## Testing

```bash
PYTHONPATH=. python services/auto_client_pipeline_test.py
PYTHONPATH=. python -m pytest tests/
```

## Documentation index

| Doc | Topic |
|-----|-------|
| [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) | Platform overview |
| [VERTICALS.md](VERTICALS.md) | Business verticals |
| [REQUEST_LIFECYCLE.md](REQUEST_LIFECYCLE.md) | Lead/request flow |
| [ROUTING.md](ROUTING.md) | Entry points |
| [TELEGRAM_INTERACTION.md](TELEGRAM_INTERACTION.md) | Bot UX patterns |
| [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) | ORM and tables |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deploy guide |
| [ROLES_AND_PERMISSIONS.md](ROLES_AND_PERMISSIONS.md) | Auth model |

Legacy docs: [architecture.md](architecture.md), [developer_guide.md](developer_guide.md), [technical_debt.md](technical_debt.md)
