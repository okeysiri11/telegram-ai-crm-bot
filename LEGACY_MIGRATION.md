# Legacy Migration Guide

Platform Core is the **default execution path**. Legacy Telegram CRM code remains
operational through the `platform_legacy` Compatibility Layer until each subsystem
reaches `REMOVED` state.

## Compatibility Guarantees

- No business functionality breaks during migration
- Transitions are reversible via feature flags or `migration_manager.rollback()`
- Legacy is reachable **only** through `platform_legacy` adapters
- Direct imports of `handlers`, `database_legacy`, `services.pg_*`, `openrouter` are forbidden outside `platform_legacy/`

## Migration Matrix

| Subsystem | State | Platform Module | Legacy Module | Legacy Flag |
|-----------|-------|-----------------|---------------|-------------|
| ai | LEGACY | `platform_ai` | `openrouter.py` | `legacy_ai` |
| configuration | PLATFORM | `platform_configuration` | `database_legacy (config keys)` | `legacy_configuration` |
| managers | MIGRATING | `platform_operations` | `services/pg_manager_delivery_engine` | `legacy_managers` |
| notifications | MIGRATING | `platform_sdk.notification_provider` | `services/notification_service` | `legacy_notifications` |
| repositories | LEGACY | `repositories` | `database_legacy.py` | `legacy_database` |
| requests | MIGRATING | `platform_sdk.verticals` | `services/pg_auto_client_request_engine` | `legacy_requests` |
| scheduler | LEGACY | `platform_jobs` | `services/pg_scheduler_engine` | `legacy_scheduler` |
| telegram | LEGACY | `platform_sdk` | `handlers.py` | `legacy_handlers` |
| users | MIGRATING | `platform_identity` | `services/pg_platform_permissions_engine` | `legacy_users` |
| workflow | MIGRATING | `platform_workflows` | `platform_workflows/adapters/legacy_rules` | `legacy_workflow` |

## Feature Flags (runtime, no code deploy)

| Flag | Env Variable | Default |
|------|--------------|---------|
| `legacy_ai` | `LEGACY_AI` | `False` |
| `legacy_configuration` | `LEGACY_CONFIGURATION` | `False` |
| `legacy_managers` | `LEGACY_MANAGERS` | `False` |
| `legacy_notifications` | `LEGACY_NOTIFICATIONS` | `False` |
| `legacy_database` | `LEGACY_DATABASE` | `False` |
| `legacy_requests` | `LEGACY_REQUESTS` | `False` |
| `legacy_scheduler` | `LEGACY_SCHEDULER` | `False` |
| `legacy_handlers` | `LEGACY_HANDLERS` | `False` |
| `legacy_users` | `LEGACY_USERS` | `False` |
| `legacy_workflow` | `LEGACY_WORKFLOW` | `False` |

## Remaining Legacy Components

- **ai** (LEGACY): `openrouter.py`
- **managers** (MIGRATING): `services/pg_manager_delivery_engine`
- **notifications** (MIGRATING): `services/notification_service`
- **repositories** (LEGACY): `database_legacy.py`
- **requests** (MIGRATING): `services/pg_auto_client_request_engine`
- **scheduler** (LEGACY): `services/pg_scheduler_engine`
- **telegram** (LEGACY): `handlers.py`
- **users** (MIGRATING): `services/pg_platform_permissions_engine`
- **workflow** (MIGRATING): `platform_workflows/adapters/legacy_rules`

## Removal Roadmap

| Phase | Goal |
|-------|------|
| Phase 1 (current) | Platform Core default; legacy via Compatibility Layer + flags |
| Phase 2 | Subsystems move LEGACY → MIGRATING → PLATFORM |
| Phase 3 | Legacy flags default off; compatibility path opt-in only |
| Phase 4 | REMOVED state — legacy modules disabled entirely |

## Deprecated APIs

- `database_legacy` → repositories.* + database.session (removal: None)
- `handlers.router` → platform_sdk + platform_workflows (removal: None)
- `openrouter.ask_openrouter` → platform_ai.llm (removal: None)
- `services.pg_*` → platform_legacy adapters → platform services (removal: None)

## Operations

- `GET /management/v1/migration` — full report
- `GET /management/v1/migration/status` — subsystem states
- `GET /management/v1/migration/coverage` — platform vs legacy hits
- `GET /management/v1/migration/deprecated` — deprecated API registry
- `GET /management/v1/migration/feature-flags` — runtime flags
- `GET /management/v1/migration/health` — migration health

## Disabling Legacy Completely

Set all subsystems to `REMOVED` via `migration_manager.set_state()` and ensure all
`legacy_*` flags are `false`. Legacy adapters become unreachable; Platform Core only.
