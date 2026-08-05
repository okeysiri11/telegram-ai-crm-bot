# Enterprise Shell

**Sprint:** 28.5  
**Package:** `src/web/src/shell/enterprise/`  
**Entry:** `EnterpriseShell` (Providers) · `enterpriseShellRuntime` · `FullLayout` chrome

## Role

The Enterprise Shell is the **single SPA runtime entry** for the Enterprise Platform. It orchestrates navigation, module registration, session restore, search projection, activity timeline, and the persistent runtime bar — without replacing Desktop Window Manager, Runtime Engine, AI Studio, Production Center, Enterprise City, or Integration Hub.

## Architecture

```
Providers
  └── EnterpriseShell (prefs + module visit tracking)
        └── routes (FullLayout | DesktopShell | …)
              FullLayout
                ├── Sidebar ← shellModuleRegistry + preferences
                ├── LeftDock / ActivityPanel ← activity timeline
                └── ShellRuntimeBar ← Runtime Engine metrics + StatusBar

enterpriseShellRuntime.startup()
  ├── hydrate shell preferences
  ├── registerIntegrationSearch + refreshShellSearch + quick actions
  ├── runtimeEngine.start()
  ├── sessionCoordinator.restoreAll()
  └── event bus → recent modules / activity journal
```

## Responsibilities

| Concern | Implementation |
|---------|----------------|
| Global navigation | `Sidebar` + `shellModuleRegistry.toNavItems()` |
| Favorites / pins / recents | `shellPreferencesStore` (`ews_shell_prefs_v1`) |
| Module categories | `ShellModuleCategory` on registry |
| Unified search | `shellSearch` → existing `searchIndex` |
| Quick actions | `shellQuickActions` → Command / search |
| Activity timeline | `activityTimeline` (journal · notifications · bus) |
| Runtime bar | `ShellRuntimeBar` (CPU · Mem · Queue · Jobs · AI · Providers) |
| Lifecycle | `enterpriseShellRuntime` startup / restore / shutdown / init / unload |

## Non-goals

- Does **not** rewrite Desktop WM or Workspace Manager  
- Does **not** create a second event bus or job engine  
- Does **not** replace `ENTERPRISE_SHELL_NAV` catalog used by legacy tests — registry is the live nav source  

## Related docs

- [`MODULE_REGISTRY.md`](./MODULE_REGISTRY.md)  
- [`SPRINT_28_5_RESULT.md`](./SPRINT_28_5_RESULT.md)  
- [`INTEGRATION_HUB.md`](./INTEGRATION_HUB.md)  
- [`RUNTIME_ENGINE.md`](./RUNTIME_ENGINE.md)  
- [`WINDOW_MANAGER.md`](./WINDOW_MANAGER.md)  
