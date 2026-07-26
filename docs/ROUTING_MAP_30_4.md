# Routing Map — Sprint 30.4

## Shell & identity

| Route | Surface |
|-------|---------|
| `/login` · `/auth/*` | Auth layout |
| `/workspace` | Workspace home |
| `/identity/*` | Identity Center UI |
| `/navigation` | Navigation platform |
| `/settings` | Settings |
| `/command-center` | Global Command Center |
| `/platform-builder/*` | Platform Builder hubs |

## Portals

| Route | Notes |
|-------|-------|
| `/portals/customer` | Customer portal shell |
| `/portals/employee` | Employee portal shell |
| `/portals/owner` | Owner / executive shell |
| `/portals/mission-control` | Redirect → PB Mission Control |

## Workspace modules (module loader)

Pattern: `/workspace/:module` · `/workspace/:module/:sub`

| Module key | Title |
|------------|-------|
| `crm` `erp` `finance` `analytics` `marketplace` `ai` | Universal |
| `hr` `docs` `reports` `workflows` | Shared ops |
| `auto` | Automotive |
| `beauty` | Beauty |
| `cafe` | Cafe |
| `agro` | Agriculture |
| `drone` | Drone |
| `legal` | Legal |
| `crypto` | Crypto (Bidex) |

Registry: `src/web/workspace/managers/moduleRegistry.ts`

## Mission Control & ecosystems

| Route | Role |
|-------|------|
| `/platform-builder/mission-control` | Executive Mission Control |
| `/platform-builder/business-ecosystem` | Ecosystem foundation UI |
| `/platform-builder/command-center` | Command Center OS |

## Guards

- `ProtectedRoute` — requires authenticated session  
- `PermissionGuard` — requires workspace permission or admin / platform_owner  
- Sidebar — `navigationManager.forTenant(tenantId, permissions)`  
