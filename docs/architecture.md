# Architecture Overview

## Goals

Transform the Telegram CRM bot into a **modular automotive platform** without disrupting live user flows.

## Principles

1. **Strangler Fig** — new code in `src/` absorbs domains gradually.
2. **No big-bang rewrite** — legacy routers/handlers remain authoritative until cutover.
3. **Interfaces first** — DI container, storage, notifications, events defined before migration.
4. **Domain boundaries** — `src/domains/<name>/{models,schemas,services,repositories,routers,events}`.

## Package map

```
src/
  domains/          # 14 domain scaffolds (empty facades)
  events/           # LeadCreated, LeadAssigned, … + EventDispatcher
  platform/
    notifications/  # NotificationProvider stack
    storage/        # StorageProvider stack
    permissions/    # Role/Permission dataclasses
    analytics/      # LeadMetrics / ManagerMetrics / RevenueMetrics
container.py        # DI registry (not wired into startup yet)
api/v1/             # /api/v1 stub routes (501 scaffold)
```

## Legacy runtime (unchanged)

- `routers/*` — Auto Client / Dealer / Manager CRM
- `handlers.py` + `*_handlers.py`
- `services/pg_*` engines
- `services/crm_event_bus.py` + root `events.py`

## Wiring status

| Component | Wired to bot startup? |
|-----------|----------------------|
| `container.py` | No (opt-in import) |
| `src/events` | No |
| `api/v1` | No (call `register_api_v1_routes`) |
| Domain packages | Scaffold only |

## Related docs

- [System overview](SYSTEM_OVERVIEW.md)
- [Developer guide](DEVELOPER_GUIDE.md)
- [Verticals](VERTICALS.md)
- [Current architecture audit](architecture/current_architecture.md)
- [Deployment](deployment.md)
- [Database](database.md)
- [FSM](fsm.md)
- [Events](events.md)
- [Permissions](permissions.md)
- [Technical debt](technical_debt.md)
