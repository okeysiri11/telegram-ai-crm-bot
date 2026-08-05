# Tenant Isolation — Sprint 30.0

**Helpers:** `repositories/tenant_scope.py`  
**Audit script:** `scripts/audit_tenant_isolation.py` → `docs/TENANT_ISOLATION_AUDIT.md`  
**Debt:** TD-58

## Rules

1. Any query against a model with `tenant_id` **must** call `apply_tenant_filter` or an equivalent explicit `WHERE tenant_id = :id`.
2. Default `required=True` (or config `REQUIRE_TENANT_FILTER=true`) — missing tenant raises `TenantIsolationError`.
3. Cross-tenant admin/ops tools may pass `required=False` **only** with an explicit audit log of the bypass.
4. Use `assert_entity_tenant(entity, tenant_id)` before mutating loaded entities.

## Example

```python
from repositories.tenant_scope import apply_tenant_filter, require_tenant_id

tid = require_tenant_id(tenant_id)
stmt = apply_tenant_filter(select(Car), Car, tid)
```

## Bot middleware

`middleware/tenant_middleware.py` injects `tenant_ctx` / `tenant_id` into aiogram handlers via `TenantContextService`.

## Verification

```bash
.venv/bin/python scripts/audit_tenant_isolation.py
```

Findings are heuristic (query without tenant mention) — triage before treating as confirmed leaks.

## Enterprise Web (Sprint 30.9)

- `apiClient` sends `X-Tenant-Id`, `X-Organization`, `X-Workspace`, Bearer.
- Client helper: `src/web/src/security/tenantGuard.ts` (`validateTenantContext`, `assertSameTenant`).
- AI tasks remain org/workspace isolated via `aiTaskSecurity.canAccessTaskResource`.
- Nginx forwards tenant headers to `/api/`.
