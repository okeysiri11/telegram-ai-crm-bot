# RBAC Audit — Sprint 37.2

## Model

| Layer | Component | Roles |
|-------|-----------|-------|
| Platform IAM | `platform_identity` | owner, administrator, readonly, service, … |
| Management API | `ManagementRole` | owner ≥ administrator ≥ readonly |
| Permission Engine | `permission_resolver` | permission strings + `*` |
| Skills | `SkillPermissions` | elevated scopes require plugin_id |

## Canonical role resolution

1. Authenticate → `Principal` (JWT claims / API key / Telegram owner).
2. `require_role` calls `identity_service.resolve_management_role(principal=…)` (**Sprint 37.2** — JWT roles honored).
3. Fine-grained checks via `permission_resolver.allow(ctx, action)`.

## Verified behaviors

| Check | Result |
|-------|--------|
| Owner `*` allows workflow.execute | PASS |
| Readonly without execute perm denied | PASS |
| Telegram header alone on management API | DENIED |
| Expired JWT | 401 |
| Admin-only management routes | Decorated with ADMINISTRATOR/OWNER |
| Elevated skills without plugin_id | DENIED |

## Gaps (not Critical)

| Pri | Finding | Effort |
|-----|---------|--------|
| P1 | Not every domain route uses Permission Engine (some role-only) | 3d |
| P2 | Builder / Marketplace / Creative / Voice deepen resource-level ACL | 4–6d |
| P2 | Workspace isolation is registry-level; row filters incomplete | 3d |

## Verdict

**RBAC fully validated** for Management + Permission Engine + Skills elevated gate. Residual: broaden Permission Engine to all vertical APIs (P1/P2).
