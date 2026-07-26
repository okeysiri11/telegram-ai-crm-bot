# Administrator Guide — Sprint 32.0

## Access

- Auth: Enterprise ISAM (`/api/enterprise-isam/v1`) + JWT sessions
- Web: `ProtectedRoute`, `PermissionGuard`, Identity Center pages
- Roles: owner / admin / operator journeys on Pilot Dashboard

## Platform surfaces

| Surface | Route | Purpose |
|---------|-------|---------|
| Pilot Dashboard | `/pilot` | Unified pilot ops |
| Production Readiness | `/pilot/production` | EPD gate + health probes |
| Mission Control | `/platform-builder/mission-control` | Cross-ecosystem ops |
| AI Team | `/platform-builder/ai-team` | Shared AI activation |
| Workspaces | `/workspace/{auto,beauty,cafe,agro,legal,crypto,drone}` | Live pilots |

## Configuration

- Web: `src/web/src/config/webConfig.ts` (`VITE_API_BASE`)
- Secrets: environment / vault refs (see Deployment Guide) — no secrets in git
- Rate limits: existing API gateway + platform_security rate limit modules

## Do not

- Create new Business Ecosystems
- Duplicate auth, AI, or gateway layers
- Bypass RBAC for “pilot convenience”
