# Developer Guide

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # or fill .env
docker compose up -d postgres redis
alembic upgrade head
PYTHONPATH=. python bot.py
```

## Project layout

```
routers/                 Telegram routers (client, manager, history)
services/                Business engines
services/storage/        Media storage providers
api/                     HTTP API (health + CRM REST)
database/models/         SQLAlchemy models
migrations/versions/     Alembic migrations
docs/                    Architecture / deploy / API docs
```

## Adding a permission

1. Add code to `PLATFORM_PERMISSIONS` in `services/pg_platform_permissions_engine.py`
2. Map it in `ROLE_PERMISSION_MAP`
3. Restart bot — `ensure_seeded()` runs on startup

## Adding an audit event

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

## Running tests

```bash
PYTHONPATH=. python services/auto_client_pipeline_test.py
PYTHONPATH=. python services/crm_platform_regression_test.py
PYTHONPATH=. python services/production_hardening_test.py
```

## FSM rules

- Never leave user stuck after request submit — call `await state.clear()`
- Any main menu button must clear FSM before starting a new flow
- VIN is optional and validated only on voluntary entry

## Escalation worker

Call periodically (e.g. scheduler job every minute):

```python
from services.pg_escalation_engine import EscalationEngineV1
await EscalationEngineV1.process_pending()
```

## Media

```python
from services.storage import get_storage_provider

storage = get_storage_provider()
media = await storage.store(file_id=telegram_file_id, data=optional_bytes)
```
