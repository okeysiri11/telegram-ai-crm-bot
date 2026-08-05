# Authorization — Sprint 30.0

**Package:** `platform_security.permission_engine`  
**Additive to:** `platform_identity.permission_service`, `platform_security.permissions.PermissionManager`

## Components

| Component | Role |
|---|---|
| `PermissionContext` | Principal roles/permissions/tenant/attributes |
| `RoleResolver` | Expands roles via `RoleManager` inheritance |
| `PolicyEvaluator` | Allow/deny + optional ABAC attribute match |
| `PermissionCache` | Short TTL effective-permission cache |
| `PermissionResolver` | Facade: `allow(ctx, permission, resource=...)` |

## Usage

```python
from platform_security.permission_engine import PermissionContext, permission_resolver

ctx = PermissionContext.from_principal(principal, tenant_id=str(tenant_id))
if not permission_resolver.allow(ctx, "workflow.execute", resource=workflow_id):
    raise PermissionError("denied")
```

## Compatibility

- Does **not** replace IAM permission catalogs or Management RBAC.
- Existing `PermissionManager.check` remains the low-level matcher.
- Star permission (`*`) and `prefix.*` wildcards behave as before.
