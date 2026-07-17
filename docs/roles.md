# Roles and access

## System roles

Defined in `services/system_roles.py`:

| Role | Code | Auto-assign leads |
|------|------|-------------------|
| Super Admin | `SUPER_ADMIN` | No |
| Auto Manager | `AUTO_MANAGER` | Yes (AUTO only) |
| Agro Manager | `AGRO_MANAGER` | Yes (AGRO only) |
| Client | `CLIENT` | No |

## Platform actors (production)

| Actor | Role | Vertical | Telegram |
|-------|------|----------|----------|
| Tony Soprano | SUPER_ADMIN / OWNER | all (view) | `OWNER_ID` |
| Boroda_0003 | AUTO_MANAGER | auto | `DEFAULT_AUTO_MANAGER_ID` |
| Christopher Moltisanti | AGRO_MANAGER | agro | `DEFAULT_AGRO_MANAGER_ID` |

Seeded by `VerticalRoutingEngineV1.ensure_platform_actors()` on startup.

## Permission engine

Live tables: `permission_engine_roles`, `permission_engine_permissions`, `permission_engine_user_roles`.

Access checks:

```python
from services.role_service import role_service

allowed = await role_service.has_permission(telegram_id, "leads.assign")
```

Legacy alias: `has_permission()` → PostgreSQL when `POSTGRES_ONLY=true`.

## RoleService API

```python
await role_service.has_permission(telegram_id, "admin.access")
await role_service.assign_role(telegram_id=..., role_code="AUTO_MANAGER")
await role_service.ensure_platform_roles_seeded()
```

## UserService role methods

```python
await user_service.assign_role(telegram_id=..., role_code="CLIENT")
await user_service.assign_verticals(telegram_id=..., verticals=["auto"])
await user_service.check_access(telegram_id=..., permission="leads.view")
```

See [ROLES_AND_PERMISSIONS.md](ROLES_AND_PERMISSIONS.md) for full matrix.
