# Permissions

## Production (live)

- Tables: `permission_engine_roles`, `permission_engine_permissions`, `permission_engine_role_permissions`
- Seeder: `services/pg_platform_permissions_engine.py`
- Roles: OWNER, ADMIN, MANAGER, AUTO_MANAGER, DEALER_MANAGER, CLIENT, AI_AGENT

## Scaffold (night task)

Dataclasses in `src/platform/permissions` and `src/domains/permissions/models`:

- `Role`
- `Permission`
- `RolePermission`

**Not** registered on SQLAlchemy `Base` — avoids mapper conflicts with existing ORM classes.

## Migration file

`f9u123456789` is a **no-op marker**. New physical tables are deferred until strangler cutover decides canonical schema (`permission_engine_*` vs domain schemas).

## Next step recommendation

1. Treat `permission_engine_*` as system of record.
2. Add facade `src/domains/permissions/services/permission_service.py` wrapping existing repositories.
3. Stop adding parallel RBAC tables (`rbac_v2_*` legacy debt).
