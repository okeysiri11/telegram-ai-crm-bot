# Sprint 33.2.1 — Platform Stability & Render Loop Audit

**Status:** Complete  
**Scope:** Frontend only (architecture / rendering correctness). No UI redesign, API, backend, or route removals.

## Verdict

Shared store and selector bugs that caused **Maximum update depth exceeded** on some routes (while others worked) are fixed. Major modules keep **RouteErrorBoundary** isolation. Platform route sync is idempotent.

---

## 1. Render loops found

| # | Location | Cause |
|---|----------|--------|
| 1 | `useSharedContext` (`useIntegrationHub.ts`) | Selector returned a **new object** every `getSnapshot` → infinite `useSyncExternalStore` updates on Desktop / AI Studio / Production |
| 2 | `ExecutiveSummaryDashboard` | `useNotificationStore(s => s.items.filter(...))` returned a **new array** every snapshot → loop on Simple `/dashboard` |
| 3 | `ProjectExplorer` / `ProjectDashboard` | `useProductionStore(s => s.projectDashboard(id))` returned a **new object** every snapshot → loop on AI Studio projects view |

## 2. Recursive state updates

| Area | Issue | Fix |
|------|--------|-----|
| `integrationContextStore.syncFromRoute` | Always `set()` with new `syncedAt` | Skip `set` when context fields unchanged |
| `productionStore.setView` / `openStudio` | Unconditional `set` | Equality guards |
| `shellPreferencesStore.rememberModule` | Rewrote `recentModuleIds` every visit | Early return if already first |
| `navStore.visit` | Same pattern | Early return if already first |
| `experienceModeStore.setMode` | No-op missing | Guard |
| `navAccordionStore.expand` | No-op missing | Guard |
| `roleSwitcherStore.setRole` | No-op missing | Guard |
| `shellPreferencesStore.setSidebarCollapsed` | No-op missing | Guard |
| `contextEngine.pushPage` / `patch` | Always mutated | Idempotent writes |

## 3. Recursive store updates

- Accordion `ensureForRoute` only expands when group differs (via `getState()`, not unstable selector deps).
- Workspace `setWorkspace` already skipped unchanged patches.
- Integration hub no longer publishes `context_changed` when surface/workspace/org/project unchanged (existing logic retained).

## 4. Unstable dependencies

| Pattern | Fix |
|---------|-----|
| `useEffect(..., [params.get("studio"), params.get("tab")])` | Bind `studioParam` / `tabParam` primitives |
| Command Center / Navigation context `value={{...}}` | `useCallback` + `useMemo` |
| `LiveDashboardDataProvider` inline `refreshHealth` | `useCallback` |
| Zustand object/array selectors | `useShallow` or derive with `useMemo` outside selector |

## 5. Unnecessary rerenders (reduced)

- Context providers memoized.
- Mode / accordion / prefs / nav recent skip no-op writes.
- Live enterprise snapshot/`busy` already guarded (prior pass).

## 6–8. Highest render / remount risk (pre-fix)

1. Any consumer of `useSharedContext` (Desktop shell, AI Studio, Production).
2. Simple Mode dashboard (`ExecutiveSummaryDashboard`).
3. AI Production project dashboard (`projectDashboard` selector).
4. Sidebar accordion route sync (mitigated via `getState().ensureForRoute`).

## 9. Performance / correctness improvements applied

- Stable shared context selection (`useShallow`).
- Idempotent route → context sync.
- Stable provider values.
- Module error boundaries on Dashboard, Owner, Calendar, Tasks, Notifications, Settings (Hub modules already wrapped).
- Route-walk smoke test asserting one store write per path.

## 10. Files changed (primary)

- `src/web/src/integration-hub/useIntegrationHub.ts`
- `src/web/src/integration-hub/integrationContextStore.ts`
- `src/web/src/ai-production-studio/productionStore.ts`
- `src/web/src/ai-production-studio/AIProductionCenterPage.tsx`
- `src/web/src/ai-production-studio/ProjectExplorer.tsx`
- `src/web/src/ai-studio/AIStudioPage.tsx`
- `src/web/src/ux-revolution/ExecutiveSummaryDashboard.tsx`
- `src/web/src/ux-revolution/experienceModeStore.ts`
- `src/web/src/ux-revolution/navAccordionStore.ts`
- `src/web/src/navigation/roleSwitcherStore.ts`
- `src/web/src/navigation/navStore.ts`
- `src/web/src/navigation/Sidebar.tsx`
- `src/web/navigation/components/NavigationProvider.tsx`
- `src/web/command-center/components/CommandCenterProvider.tsx`
- `src/web/command-center/managers/contextEngine.ts`
- `src/web/src/shell/enterprise/shellPreferencesStore.ts`
- `src/web/src/live-dashboard/LiveDashboardDataContext.tsx`
- `src/web/src/live-ops/useLiveEnterprise.ts`
- `src/web/src/workspace/workspaceStore.ts`
- `src/web/src/App.tsx`
- `src/web/src/config/webConfig.ts` → sprint `33.2.1`
- `src/web/src/test/platformStability_33_2_1.test.tsx`
- `docs/PLATFORM_STABILITY_33_2_1.md`

## 11. Test results

```text
Test Files  6 passed (6)
Tests       90 passed (90)
```

Suites: `platformStability_33_2_1`, `intelligentNav`, `uxRevolution`, `integrationHub`, `renderLoop.smoke`, `foundation`.

No Maximum update depth errors in smoke probes.

## Platform walkthrough checklist

| Mode | Expectation |
|------|-------------|
| Simple | Dashboard Executive Summary loads; Workspace / Business / AI accordion only |
| Pro | Full groups except Owner (unless owner view) |
| Owner | Owner group available; `/owner` bounded |
| All routes in smoke list | `syncFromRoute` twice → single subscription write |

## Out of scope (intentional)

- UI redesign, backend, API contracts, route map changes, feature removal.
