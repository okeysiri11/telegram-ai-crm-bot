# Database — PostgreSQL production

## Single source of truth

Production uses **PostgreSQL 16+** exclusively for persistent entities:

- users, roles, permissions
- client requests (`client_requests`, `auto_client_requests_v1`)
- leads, deals, pipeline boards
- audit logs (`platform_audit_log`)

## Connection

```
postgresql+asyncpg://postgres@localhost:5432/ai_ecosystem
```

| Setting | Module |
|---------|--------|
| `DATABASE_URL` | `config.py`, `database/engine.py` |
| Engine | `sqlalchemy.ext.asyncio.create_async_engine` |
| Driver (async) | **asyncpg** |
| Driver (Alembic) | **psycopg2** |
| Sessions | `database/session.py` → `get_session()` |

## POSTGRES_ONLY mode

```env
POSTGRES_ONLY=true
```

When enabled (default):

- `ensure_user`, `create_request`, `log_audit`, `has_permission` → PostgreSQL services
- New code must not use `sqlite3` or `memory.db`

## Repositories (SQL layer)

| Repository | File |
|------------|------|
| UserRepository | `repositories/user_repository.py` |
| RequestRepository | `repositories/request_repository.py` |
| ManagerRepository | `repositories/manager_repository.py` |

Services **must not** contain raw SQL.

## Migrations

```bash
alembic upgrade head
```

- 105+ migration files in `migrations/versions/`
- Current head tracked in `alembic_version` table

## Deprecated: SQLite

| Item | Status |
|------|--------|
| `database_legacy.py` | Deprecated — shimmed critical functions |
| `memory.db` | Do not use in production |
| `from database import ...` | Migrate to `services/*_service.py` |

Run audit: `PYTHONPATH=. python3 scripts/audit_sqlite_usage.py`

## FSM storage (not entity DB)

| Backend | Purpose |
|---------|---------|
| Redis | Persistent FSM (recommended) |
| MemoryStorage | Dev fallback — **not** for users/requests |
