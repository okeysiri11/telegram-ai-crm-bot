# Current Architecture Map (Audit Snapshot)
# Generated as part of NIGHT TASK — Platform Architecture Upgrade
# Source of truth for pre-migration state. No legacy code was moved.

## Layer inventory

| Layer | Location | Count (approx) | Notes |
|-------|----------|----------------|-------|
| Routers | `routers/` | 7 | Modular Telegram entry (auto client/dealer/manager) |
| Handlers | `*_handlers.py` (root) | 24 | Monolithic legacy Telegram handlers |
| Services | `services/` | ~204 | Business engines (`pg_*`) + utilities |
| Repositories | `repositories/` | ~99 | SQLAlchemy data access |
| Models | `database/models/` | ~109 | ORM entities |
| Middleware | `middleware/` | 3 | Entry-point + tenant |
| States | `states/` | 2 | FSM groups (`AutoClientFlow`, …) |
| API | `api/` | 6+ | Health + gateway + CRM REST |

## Runtime composition

```
bot.py → main.py → bootstrap.py (Dispatcher + FSM storage)
                 → startup.py (register_routers, API, scheduler, escalation)
                 → polling

register_routers order (startup.py):
  1. routers.auto_client_router
  2. routers.auto_dealer_router
  3. routers.client_history_router
  4. routers.manager_crm_router
  5. routers.manager_debug_router
  6. routers.auto_hub_router
  7. auto_vertical_handlers
  8. handlers (legacy mega-router)
```

## Dependency graph (logical)

```mermaid
flowchart TB
  TG[Telegram Updates] --> MW[middleware.entry_point / tenant]
  MW --> R[routers/*]
  MW --> H[handlers.py + *_handlers.py]
  R --> S[services/*]
  H --> S
  H --> KB[keyboards.py]
  R --> KB
  S --> Repo[repositories/*]
  Repo --> Models[database/models/*]
  Models --> DB[(PostgreSQL)]
  S --> EB[crm_event_bus / events.py]
  S --> NC[notification_center]
  S --> ST[storage providers]
  API[api/server.py] --> S
  API --> Health[/health /metrics]
```

## Import graph (hot paths)

```
routers/auto_client_router
  → services.auto_client_flow_engine
  → services.pg_auto_client_request_engine
  → services.pg_entry_point_engine
  → services.pg_vertical_onboarding_engine
  → states.entry_flow_states
  → routers.auto_hub_router   ⚠️ cross-router import

pg_auto_client_request_engine
  → pg_manager_delivery_engine
  → pg_client_request_crm_engine
  → pg_marketplace_listing_engine

pg_client_request_crm_engine
  → platform_audit / lead_sla / notification hooks
  → crm_event_bus (lazy)

auto_vertical_handlers
  → many pg_* engines + vin_decoder + billing
  → automotive_partner_handlers
```

## Cyclic / near-cyclic dependencies

| Cycle risk | Description | Severity |
|------------|-------------|----------|
| `auto_client_router` ↔ `auto_hub_router` | Hub imports menu helpers; client imports hub open/return | Medium |
| `services` ↔ lazy `services` | Widespread lazy imports to break cycles (crm_event_bus, lead engines) | Medium |
| `handlers` ↔ `keyboards` ↔ `services` | Flat imports amplify coupling | High |
| SQLAlchemy model duplicates | Multiple `Role`/`Permission`/`UserRole` namings historically | High (mapper errors) |
| Root `events.py` vs future `events/` package | Name collision risk if package created at repo root | Medium — mitigated via `src/events/` |

## High-coupling modules

| Module | Lines | Coupling reason |
|--------|------:|-----------------|
| `handlers.py` | ~5081 | God router: CRM, menus, finance, owner panels |
| `keyboards.py` | ~2020 | Shared UI for all verticals |
| `database_legacy.py` | ~11143 | Legacy SQLite/ORM surface |
| `auto_vertical_handlers.py` | ~1256 | Cars + billing + AI + partners |
| `pg_scheduler_engine.py` | ~790 | Job registry hub |
| `pg_automotive_operations_engine.py` | ~1053 | Ops + SLA + tasks |

## God classes / oversized engines

- `handlers.py` — multi-domain Telegram handler mega-file
- `AutomotiveOperationsEngine`, AI Procurement/Advertising/Sales engines — multi-concern
- `ManagerDeliveryEngineV1` — delivery + auth checks + keyboards + debug
- `EntryPointEngineV1` — routing + session + lead ingest

## Duplicate logic

| Concern | Locations |
|---------|-----------|
| Notifications | `services/notification_center.py`, `src/platform/notifications`, legacy `services/notifications.py` |
| Storage | `services/storage/`, `src/platform/storage/` |
| Permissions | `permission_engine_*`, `rbac_v2_*`, `database/models/permissions.py`, platform seed engine |
| Inventory | `automotive_inventory` vehicles vs `inventory` marketplace table vs listings |
| Events | `events.py`, `services/crm_event_bus.py`, `src/events/` (new scaffold) |
| Audit | `audit_engine_logs` vs `audit_log` platform table |
| SLA | `pg_sla_tracking_v1` vs `pg_lead_sla_engine` |

## Architecture target (next phase)

Strangler pattern:

1. Keep legacy routers/handlers serving production traffic.
2. Grow `src/domains/*` + `container.py` + `src/events`.
3. Move one vertical at a time behind domain facades.
4. Retire god files incrementally after parity tests.

See also:

- `docs/architecture.md`
- `docs/technical_debt.md`
- `src/domains/`
