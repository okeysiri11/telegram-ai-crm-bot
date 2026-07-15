# Database

## Engines

- PostgreSQL via `DATABASE_URL` (`postgresql+asyncpg://…`)
- Redis optional for FSM (`REDIS_URL`)
- Legacy SQLite: `memory.db` / `database_legacy.py` (do not expand)

## Core CRM / marketplace tables (current)

| Table | Purpose |
|-------|---------|
| `auto_client_requests_v1` | Auto client leads |
| `client_requests` | Unified CRM history + funnel |
| `marketplace_listings` | Listing objects |
| `inventory` | Marketplace inventory catalog |
| `audit_log` | Platform audit trail |
| `lead_sla_records` | Lead SLA timers |
| `permission_engine_*` | Roles / permissions |
| `lead_engine_v1_leads` | Legacy lead engine |

## Alembic heads (architecture epoch)

```
… → f9s901234567 (CRM platform)
  → f9t012345678 (hardening: audit/inventory/SLA)
  → f9u123456789 (architecture scaffold marker — no-op)
```

## Conventions for domain migration

1. Prefer additive nullable columns.
2. Never require VIN.
3. New domain tables should use clear prefixes until cutover.
4. Avoid registering duplicate class names on `Base.metadata`.
