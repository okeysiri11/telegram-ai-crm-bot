# Services layer

## Overview

All business logic between Telegram routers and PostgreSQL lives in `services/*_service.py`.

Handlers **must not** call `get_session()`, `cursor.execute()`, or `sqlite3`.

## Core services

### UserService (`services/user_service.py`)

```python
from services.user_service import user_service

user = await user_service.get_user(telegram_id=123)
user = await user_service.ensure_user(telegram_id=123, full_name="...", username="...")
await user_service.assign_role(telegram_id=123, role_code="CLIENT")
await user_service.assign_verticals(telegram_id=123, verticals=["auto"])
ok = await user_service.check_access(telegram_id=123, permission="leads.view")
```

### RequestService (`services/request_service.py`)

```python
from services.request_service import request_service

req = await request_service.create_request(
    vertical="auto",
    client_telegram_id=123,
    flow_request_type="buy_car",
    description="BMW X5",
)
req = await request_service.get_request("AUTO-0001")
await request_service.change_status(request_number="AGRO-00001", new_status="IN_PROGRESS")
await request_service.assign_manager(request_number="AGRO-00001", vertical="agro")
```

### ManagerService (`services/manager_service.py`)

```python
from services.manager_service import manager_service

mgr = await manager_service.resolve_manager_for_vertical("auto")
managers = await manager_service.list_vertical_managers("agro")
is_admin = await manager_service.is_super_admin(telegram_id)
```

### RoleService (`services/role_service.py`)

```python
from services.role_service import role_service

if await role_service.has_permission(telegram_id, "admin.access"):
    ...
```

### NotificationService (`services/notification_service.py`)

```python
from services.notification_service import notification_service

await notification_service.notify_managers_new_request(
    vertical="agro",
    request_number="AGRO-00001",
    client_name="Ivan",
    product="Пшеница",
)
await notification_service.notify_status_change(
    request_number="AGRO-00001",
    old_status="NEW",
    new_status="IN_PROGRESS",
    client_telegram_id=123,
    bot=bot,
)
```

### MediaService (`services/media_service.py`)

```python
from services.media_service import media_service

ids = media_service.resolve_photo_file_ids(primary_file_id, extras)
```

## Repositories (used by services)

| Repository | Purpose |
|------------|---------|
| `UserRepository` | users, role links |
| `RequestRepository` | client_requests, auto_client_requests |
| `ManagerRepository` | vertical subscriptions |

## Legacy engines

Existing `services/pg_*_engine.py` modules remain authoritative for complex domains. New code should call `*_service.py` facades first; facades delegate to engines.

## Enforcement

```bash
PYTHONPATH=. python3 scripts/check_handler_session_access.py
PYTHONPATH=. python3 scripts/audit_sqlite_usage.py
```

## POSTGRES_ONLY shims

When `POSTGRES_ONLY=true`, these legacy calls redirect to PostgreSQL:

- `ensure_user` → `UserService`
- `create_request` → `RequestService`
- `log_audit` → `PlatformAuditEngineV1`
- `has_permission` → `RoleService`
