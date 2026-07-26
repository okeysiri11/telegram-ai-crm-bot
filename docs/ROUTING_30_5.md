# Routing Documentation — Sprint 30.5

Extends [ROUTING_MAP_30_4.md](./ROUTING_MAP_30_4.md).

## Validated surfaces

| Kind | Pattern | Guard |
|------|---------|-------|
| Shared navigation | `menuEngine` + `forTenant` | permissions |
| Nested routing | `/workspace/:module/:sub` | Protected + PermissionGuard |
| Role-based | PermissionGuard / platform_owner | RBAC |
| Workspace | `/workspace/*` | ProtectedRoute |
| Mission Control | `/platform-builder/mission-control` | ProtectedRoute |
| Portal | `/portals/*` | ProtectedRoute; MC redirects |
| Module | registry routes | soft shells |
| Pilot | `/pilot` | ProtectedRoute |

## Duplicates removed / avoided

- Ecosystem app entries no longer independently define routes (derived from registry)
- Port Enterprise launcher points at soft `/workspace/port` (generic shell resolve) — not a second agro UI
- Single Mission Control path; portal entry remains redirect only
