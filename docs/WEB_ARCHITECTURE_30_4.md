# Web Architecture — Sprint 30.4

**Platform Builder:** v1.29.0 · Sprint 30.4 · Web Foundation  
**Hub Web:** v9.4.0 (unchanged package version; sprint tag **30.4**)

## Principle

Extend and connect existing Enterprise AI Platform surfaces. **Do not** introduce parallel shells, auth stacks, or observability modules.

## Shared application shell

| Layer | Implementation | Role |
|-------|----------------|------|
| Application Shell | `FullLayout` | Sidebar + TopNavigation + main workspace container |
| Layout System | `WorkspaceLayout`, `PortalLayout`, `PlatformBuilderLayout`, `AuthLayout` | Context-specific composition |
| Navigation Framework | `menuEngine` + `navigationManager.forTenant` | Permission-aware menu surfaces |
| Workspace Container | `WorkspaceLayout` + workspace store | Org / department / project badges |
| Module Loader | `moduleRegistry` → `WorkspaceModulePage` | Soft-route shells for universal + industry modules |
| Permission Navigation | `menuEngine.forTenant` + `PermissionGuard` | RBAC-aware nav and route gates |
| Theme Integration | `themeStore` + EDS `applyTheme` | Light / dark / system |
| Responsive Foundation | Mobile drawer sidebar + `md:` breakpoints | Pilot-usable on phone and desktop |

## Identity & access (connected, not redesigned)

| Concern | Source |
|---------|--------|
| Authentication | `authStore` session (`ewp_session_v1`) |
| Authorization / RBAC | workspace permissions + `roleId` / platform_owner |
| Organization context | `workspace.company` + `X-Organization` via `apiFetch` |
| Workspace context | `workspace.project` + `X-Workspace` |
| User context | `authStore.user` |
| Session → API | `apiClient.apiFetch` attaches `Authorization: Bearer` |

Demo tokens remain for local pilots; production middleware validates real ISAM/EIC JWTs on the same header path.

## Mission Control

- Canonical hub: `/platform-builder/mission-control`
- Portal entry: `/portals/mission-control` → redirect (unchanged)
- TopNavigation quick link + application registry entry

## Telemetry

Client: `src/web/src/integrations/telemetry.ts` → existing `/api/enterprise-obs/v1` metrics + logs.  
Toggle: `webConfig.telemetryEnabled` / `VITE_TELEMETRY_ENABLED`.

## Explicit non-goals

- New `platform_*` packages  
- Redesigning Mission Control, Command Center, or vertical backends  
- Parallel design systems  
