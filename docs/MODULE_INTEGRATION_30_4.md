# Module Integration — Sprint 30.4

## How modules load

1. User navigates to `/workspace/{key}`  
2. `App` route renders `WorkspaceModulePage` inside `ProtectedRoute`  
3. `moduleRegistry.resolve(key)` supplies metadata  
4. `PermissionGuard` checks module permissions  
5. `WorkspaceLayout` → `FullLayout` provides shared shell  

No vertical UI is reimplemented inside the shell. Shells only expose composition links (Builder, Portal, API hints).

## Business ecosystem connection points

| Ecosystem | Route | API hint (ownership unchanged) | Shell status |
|-----------|-------|--------------------------------|--------------|
| Automotive | `/workspace/auto` | `/api/auto/v1` | Connected |
| Beauty | `/workspace/beauty` | platform_beauty / BOS | Connected |
| Cafe | `/workspace/cafe` | foundation catalog | Connected (shell) |
| Agriculture | `/workspace/agro` | `/api/agro/v1` · agro-enterprise | Connected |
| Drone | `/workspace/drone` | foundation catalog | Connected (shell) |
| Legal | `/workspace/legal` | `/api/legal-enterprise/v1` | Connected |
| Crypto (Bidex) | `/workspace/crypto` | `/api/crypto-enterprise/v1` | Connected |

Application registry entries mirror the same routes for navigation search / launchers.

## Navigation wiring

- Menu group `ecosystems` in `menuEngine`  
- Portal pages list all seven ecosystems  
- Sidebar footer lists ecosystem links from `moduleRegistry.ecosystems()`  

## Duplication check

| Temptation | Decision |
|------------|----------|
| New portal framework | Reuse `PortalLayout` |
| New Mission Control | Reuse PB hub |
| New OBS stack | Reuse enterprise-obs |
| Per-industry auth | Reuse `authStore` + `apiFetch` |
