# Sprint 28.5 — Enterprise Shell & Navigation Runtime

**Phase:** Enterprise Platform v9  
**Priority:** CRITICAL  
**App:** `src/web` · sprint `28.5`  
**Constraint:** Unify shell/nav on existing Desktop · WM · Workspace · Dashboard · CC · City · Studio · Production · Event Bus — no redesign.

## Implementation summary

One Enterprise Shell runtime:

- `enterpriseShellRuntime` — startup · restore · shutdown · module init/unload  
- `shellModuleRegistry` — dynamic module projection + categories  
- `shellPreferencesStore` — favorites · pins · recents · category collapse  
- `shellSearch` / `shellQuickActions` — unified search + quick actions into existing `searchIndex`  
- `activityTimeline` — journal · notifications · event bus  
- `EnterpriseShell` + `ShellRuntimeBar` wired through Providers / FullLayout  
- Sidebar / LeftDock consume registry + preferences  

## Architecture

```
Enterprise Shell
  ├── Module Registry  → Sidebar / Dock / Search
  ├── Preferences      → pin · favorite · recent
  ├── Search + QA      → searchIndex (no second engine)
  ├── Activity         → ActivityPanel / LeftDock
  ├── Runtime Bar      → Runtime Engine metrics
  └── Lifecycle        → Integration Hub + Runtime Engine
```

## Modified / added files (primary)

**New**

- `src/web/src/shell/enterprise/shellModuleRegistry.ts`
- `src/web/src/shell/enterprise/shellPreferencesStore.ts`
- `src/web/src/shell/enterprise/enterpriseShellRuntime.ts`
- `src/web/src/shell/enterprise/shellQuickActions.ts`
- `src/web/src/shell/enterprise/shellSearch.ts`
- `src/web/src/shell/enterprise/activityTimeline.ts`
- `src/web/src/shell/enterprise/EnterpriseShell.tsx`
- `src/web/src/shell/enterprise/ShellRuntimeBar.tsx`
- `docs/ENTERPRISE_SHELL.md` · `docs/MODULE_REGISTRY.md` · `docs/SPRINT_28_5_RESULT.md`

**Updated**

- `src/web/src/shell/Providers.tsx`
- `src/web/src/layouts/FullLayout.tsx`
- `src/web/src/navigation/Sidebar.tsx`
- `src/web/src/shell/enterprise/{ActivityPanel,LeftDock,index,enterpriseShell.css,enterpriseShell.test}.ts(x)`
- `src/web/src/config/webConfig.ts` · `foundation.test.ts`
- `docs/ARCHITECTURE_MAP.md`

## Runtime summary

| Phase | Behavior |
|-------|----------|
| startup | prefs · search · QA · runtimeEngine · session restore · bus subscribe |
| ready | module visits update recents + activity |
| unload | dynamic modules only |
| shutdown | stop runtimeEngine (SPA normally keeps ready) |

## Performance

- Shell boot is idempotent (no double Runtime Engine)  
- Search upserts by id (no unbounded duplicate docs)  
- Production search capped (40 prompts / 24 generations)  
- Sidebar uses memoized nav items; prefs are localStorage-backed  
- Runtime bar uses `useSyncExternalStore` on Runtime Engine  

## Verification matrix

| Surface | Check |
|---------|--------|
| Desktop | Shell wraps Providers; Desktop WM unchanged |
| Ultrawide / 4K | FullLayout flex shell + sticky runtime bar |
| Dark / Light | Existing theme tokens on chrome |
| Restore session | `sessionCoordinator.restoreAll()` in shell startup |
| Navigation | Registry sidebar · pin/favorite/recent |
| Window Manager | Untouched store/frame |
| AI Studio / City | Routes remain; appear in registry + QA |

## Remaining work before Sprint 28.6

- Cross-surface command execution API (beyond navigate quick actions)  
- Breadcrumb deep history UI beyond TopNavigation  
- Module virtualization for 50+ dynamic plugins  
- Explicit shell shutdown on logout  
- Dual-monitor awareness for Desktop (carried from 28.4)  
- Touch polish for pin/favorite affordances  

## Tests / quality

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **189 passed** |
| build | OK |

## Readiness

| Area | Score |
|------|-------|
| Enterprise Shell | **86%** |
| Module Registry | **88%** |
| Global Navigation | **84%** |
| Enterprise Platform | **84%** |
