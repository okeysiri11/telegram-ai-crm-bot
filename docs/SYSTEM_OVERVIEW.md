# System Overview

TelegramBotCourse — multi-vertical Telegram CRM platform with PostgreSQL backend, HTTP API, and modular automotive flows.

## Purpose

The platform connects **clients**, **managers**, and **partners** across business verticals through Telegram bots. Primary production vertical is **auto** (automotive CRM). Verticals **agro**, **realty**, **legal**, and **logistics** are in partial or scaffold state.

## Architecture layers

```
Telegram / HTTP handlers     ← thin: parse input, render UI, call services
        ↓
Vertical services          ← src/verticals/{auto,agro,...}/service.py
        ↓
Business engines           ← services/pg_*_engine.py (legacy, authoritative)
        ↓
Repositories               ← repositories/* (SQLAlchemy queries only)
        ↓
ORM models                 ← database/models/*
        ↓
PostgreSQL
```

## Key packages

| Package | Role |
|---------|------|
| `routers/` | Modular Telegram routers (auto client/dealer/manager) |
| `*_handlers.py` | Feature-specific Telegram handlers |
| `services/` | Business logic engines (`pg_*`) |
| `repositories/` | Database access |
| `src/verticals/` | Vertical registry and service facades |
| `src/platform/layers/` | BaseRepository, BaseService, session policy |
| `src/domains/` | Strangler-fig domain scaffolds (future cutover) |
| `container.py` | DI registry (opt-in) |
| `api/` | HTTP REST gateway |

## Runtime entry points

| Entry | File | Description |
|-------|------|-------------|
| Bot polling | `main.py` | aiogram Dispatcher + FSM |
| Startup | `startup.py` | Router registration, scheduler, API, seeds |
| HTTP API | `api/server.py` | aiohttp on port 8080 |
| Migrations | `alembic upgrade head` | Schema changes |

## Migration strategy (Strangler Fig)

1. **Legacy remains authoritative** — `handlers.py`, `services/pg_*` continue serving production traffic.
2. **New code follows layered rules** — handlers → vertical services → engines → repositories.
3. **Domains absorb gradually** — `src/domains/*` replaces engines when parity tests exist.
4. **No big-bang rewrite** — cutover per vertical/feature.

## Session access policy

Handlers and routers **must not** import `get_session` or open `AsyncSession` directly. All database access goes through services.

Enforcement: `PYTHONPATH=. python3 scripts/check_handler_session_access.py`

## Related docs

- [VERTICALS.md](VERTICALS.md) — vertical registry
- [REQUEST_LIFECYCLE.md](REQUEST_LIFECYCLE.md) — lead/request flow
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — local setup and conventions
