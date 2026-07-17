# Roles and Permissions

## System roles

Canonical roles are defined in `services/system_roles.py`:

| Role | Code | Default verticals |
|------|------|-------------------|
| Super Admin | `SUPER_ADMIN` | auto, agro, realty, legal, logistics |
| Auto Manager | `AUTO_MANAGER` | auto |
| Agro Manager | `AGRO_MANAGER` | agro |
| Client | `CLIENT` | — |

## Manager lead statuses

Manager-facing request lifecycle (`ManagerLeadStatus`):

`NEW` → `TAKEN` → `IN_PROGRESS` → `WAITING_CLIENT` → `DEAL` → `CLOSED` / `REJECTED`

## Permission engine (production)

Live permission tables and seeder:

- Tables: `permission_engine_roles`, `permission_engine_permissions`, `permission_engine_role_permissions`
- Seeder: `services/pg_platform_permissions_engine.py`
- Roles: `OWNER`, `ADMIN`, `MANAGER`, `AUTO_MANAGER`, `DEALER_MANAGER`, `CLIENT`, `AI_AGENT`

Startup runs `ensure_seeded()` to sync role-permission mappings.

## Role access matrix

High-level capabilities per system role (`ROLE_ACCESS` in `system_roles.py`):

| Capability | SUPER_ADMIN | AUTO_MANAGER | AGRO_MANAGER | CLIENT |
|------------|:-----------:|:------------:|:------------:|:------:|
| admin_panel | ✓ | | | |
| all_verticals | ✓ | | | |
| manager_crm | ✓ | ✓ | ✓ | |
| auto_leads | ✓ | ✓ | | |
| agro_leads | ✓ | | ✓ | |
| take_lead / update_status | ✓ | ✓ | ✓ | |
| create_request | | | | ✓ |

## Legacy role aliases

Permission-engine codes map to system roles via `LEGACY_ROLE_ALIASES`:

- `OWNER`, `ADMIN`, `SUPER_MANAGER` → `SUPER_ADMIN`
- `MANAGER`, `DEALER_MANAGER`, `AUTO_MANAGER` → `AUTO_MANAGER`
- `AGRO_MANAGER` → `AGRO_MANAGER`
- `CLIENT` → `CLIENT`

## Manager authorization

Telegram manager checks use `ManagerDeliveryEngineV1.is_platform_manager(telegram_id)` which validates:

1. Configured default manager IDs (`DEFAULT_AUTO_MANAGER_ID`, `DEFAULT_DEALER_MANAGER_ID`)
2. User record + role codes from permission engine and RBAC tables

## Tenant scoping

Multi-tenant isolation is enforced by:

- `middleware/tenant_middleware.py`
- `tenant_guard_handlers.py`
- `PartnerTenantEngineV1.resolve_context()`

## Scaffold (future)

Dataclass permissions in `src/platform/permissions/` and `src/domains/permissions/` are **not** wired to production. See [permissions.md](permissions.md) for migration plan.

## Adding a permission

1. Add code to `PLATFORM_PERMISSIONS` in `services/pg_platform_permissions_engine.py`
2. Map in `ROLE_PERMISSION_MAP`
3. Restart bot — seeder runs on startup
