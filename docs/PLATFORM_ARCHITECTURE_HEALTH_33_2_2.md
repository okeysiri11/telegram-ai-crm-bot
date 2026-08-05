# Sprint 33.2.2 — Frontend Architecture Health Audit

**Status:** Report only (no functional changes)  
**Scope:** `src/web` (~881 TS/TSX files, ~112k LOC) + cross-checks vs `platform_console`  
**Date:** 2026-08-02  
**Prior:** Sprint 33.2.1 (render-loop / stability)

---

## Executive verdict

The frontend is a **layered enterprise OS shell** with intentional route aliases and an ongoing consolidation story (`integration-hub`, `enterprise-runtime`, ux-revolution intelligent nav). Health is **acceptable for shipping**, but architectural debt is concentrated in:

1. **Monolithic route registry** (`App.tsx` ~1447 lines)
2. **Parallel navigation systems** (intelligent nav vs `menuEngine` / WebCore)
3. **Overlapping app context** (WebCoreProvider vs Integration Hub)
4. **Duplicate favorites / recents / theme** stores
5. **Oversized page + store files** (City, Desktop, Production, Dashboard)

**Do not delete or consolidate without a dedicated refactor sprint.** Items marked **SAFE REMOVE** below are low-risk candidates after import/test verification.

Complexity key: **S** = &lt;1 day · **M** = 1–3 days · **L** = multi-day / multi-PR

---

## 1. Technical debt report

### 1.1 Debt heatmap

| Domain | Severity | Notes |
|--------|----------|--------|
| Route / App composition | **High** | Single mega-router; hard to review, lazy-load, or test |
| Navigation dual stack | **High** | Sidebar = intelligent nav; WebCore = legacy menuEngine |
| App context providers | **High** | WebCore + Integration Hub + LiveDashboard all mirror auth/workspace |
| Zustand store sprawl | **Med–High** | Dead `navStore`; dual favorites; theme in two places |
| Oversized UI/stores | **Med–High** | 20+ files &gt;400 lines; City page ~999 |
| Cross-app duplication | **Med** | `src/web` vs `platform_console` shells/stores |
| Legacy redirects | **Low** | Intentional bookmark aliases (~20) |
| Listener / timer hygiene | **Med** | Most React effects clean; singleton engines lack teardown |
| Circular imports | **Med** | `commandRuntime` ↔ `command-center` |

### 1.2 Provider / layout stack (current)

```
StrictMode
  └ ErrorBoundary
      └ Providers
          └ QueryClientProvider
              └ BrowserRouter
                  └ CommandCenterProvider      ← palette + global ⌘K
                      └ NavigationProvider     ← QuickSwitcher + search interval
                          └ WebCoreProvider      ← menuEngine nav (chrome ignores)
                              └ IntegrationHubBridge
                              └ EnterpriseShell    ← visit tracking
                                  └ App routes
                                        ├ WorkspaceLayout → FullLayout (primary chrome)
                                        ├ DashboardLayout → FullLayout (alias)
                                        ├ DesktopShell (/desktop)
                                        └ AuthShell (auth pages)
```

### 1.3 Duplicate / overlapping systems

#### Components

| Group | Paths | Severity | Consolidate? | Complexity |
|-------|-------|----------|--------------|------------|
| Command palettes | `navigation/components/CommandPalette.tsx` (unused) vs `command-center/.../UniversalCommandPalette.tsx` (active) + `Omnibox` | **High** | Yes — remove legacy | **S** |
| Sidebars | `src/web/.../Sidebar.tsx` vs `platform_console/.../Sidebar.tsx` | **Med** | Partial (shared primitives only) | **L** |
| Dashboards | `DashboardPage`, `ExecutiveSummaryDashboard`, `BetaHomeDashboard`, role dashboards, `LiveDashboardShell`, Production/Owner AI dashboards, console Dashboard | **High** | Partial — unify data layer, keep views | **L** |
| Error boundaries | `ErrorBoundary` + `RouteErrorBoundary` | **Low** | Share fallback UI | **S** |
| Auth shells | `auth/components/AuthShell.tsx` (active) vs `layouts/AuthLayout.tsx` (**no imports**) | **Med** | Remove AuthLayout | **S** |
| Quick actions | `workspace/.../QuickActionsBar` vs `command-center-runtime/UniversalQuickActionsBar` | **Med** | Single bar + registry | **M** |
| ProtectedRoute | web + console | **Low** | Keep separate apps | — |

#### Hooks

| Group | Paths | Severity | Complexity |
|-------|-------|----------|------------|
| Health / live status | `enterprise-runtime/useRuntimeHealth` (canonical), shell re-export, `useIntegrationRuntimeHealth`, `useLiveRuntimeMetrics`, `useEnterpriseStatus`, `useLiveEnterprise`, `useCityLiveStatus`, console `useLiveRuntime` | **Med** | **M** |
| Workspace | `workspaceStore` (tenant) + `workspaceManagerStore` (tabs) + desktop profiles | **Med** | **M** (document boundary) |
| Chrome UI | `useNavigationUi` + `useCommandCenterUi` + `useModuleContextNav` | **Low** | **M** |

#### Stores / services

| Issue | Evidence | Severity | Complexity |
|-------|----------|----------|------------|
| Dead `useNavStore` | **Zero imports** outside `navStore.ts` | **High** (noise) | **S** |
| Favorites triad | `shellPreferencesStore` + `navigation/managers/favoritesManager` + `workspace/managers/favoritesManager` | **High** | **M** |
| Theme dual SoR | `themeStore` vs `preferencesStore.theme` (unsynced) | **Med** | **S** |
| Recents dual | `lastModuleStore` vs `shellPreferences.recentModuleIds` | **Med** | **S** |
| Context dual | `WebCoreProvider` vs `integrationContextStore` / `useSharedContext` | **High** | **L** |
| Layout stores | `liveDashboardStore` + `shellLayoutStore` + `desktopStore` | **Med** | **L** |

#### Layouts

| Layout | Role | Debt |
|--------|------|------|
| `FullLayout` | Primary chrome | Canonical |
| `WorkspaceLayout` | FullLayout + embed | Canonical wrapper |
| `DashboardLayout` | **Pure alias** of FullLayout | Redundant — **S** to drop |
| `AuthLayout` | Unused | **SAFE REMOVE** |
| `EnterpriseShell` | Visit tracker only | OK; name implies more than it does |
| `DesktopShell` | Parallel chrome | By design; long-term embed routes |
| Console `AdminShell` | Marked deprecated vs `ControlShell` | Console cleanup **S** |

#### Routes

| Pattern | Severity | Notes |
|---------|----------|-------|
| ~20 `Navigate` aliases | **Low** | Keep for bookmarks; centralize map |
| `/city` **and** `/enterprise-city` | **Med** | Same page twice |
| Hub vs dedicated (`/automation-hub` vs `/automation`, `/city-hub` vs city pages) | **Med** | Confusing entry points |
| `/workspace` vs `/dashboard` dual homes | **Med** | Product ambiguity |
| Login at `/login` and `/auth/login` | **Low** | Intentional |

---

## 2. Files recommended for refactoring

| Priority | File | Lines | Why | Complexity |
|----------|------|-------|-----|------------|
| P0 | `src/web/src/App.tsx` | 1447 | Route monolith; split by domain | **L** |
| P0 | `src/web/navigation/managers/menuEngine.ts` + `WebCoreProvider.tsx` | — | Legacy nav unused by Sidebar | **L** |
| P0 | `src/web/src/shell/Providers.tsx` | — | Flatten chrome providers / context SoR | **M–L** |
| P1 | `src/web/src/enterprise-city/EnterpriseCityPage.tsx` | 999 | UI + gestures + panels | **L** |
| P1 | `src/web/src/enterprise-desktop/desktopStore.ts` | 915 | Slice by window/icon/persist/profile | **L** |
| P1 | `src/web/src/ai-production-studio/productionStore.ts` | 701 | Persist / projects / queue slices | **M** |
| P1 | `src/web/src/pages/DashboardPage.tsx` | 572 | Meta-dashboard composing many subsystems | **M** |
| P1 | `src/web/src/runtime/commandRuntime/commandRuntime.ts` | 569 | Break cycle with command-center | **M** |
| P2 | `src/web/src/onboarding/FirstEntryPage.tsx` | 663 | Step components | **M** |
| P2 | Platform-builder wizards (Concierge, Vertical, AI Builder, God Mode, …) | 575–646 | Shared wizard chrome + steps | **M** |
| P2 | `src/web/src/modules/moduleCatalog.ts` | 585 | Data modules + drop dead `shellNavFromCatalog` | **M** |
| P2 | Catalog data files (`cityCatalog`, `productionCatalog`) | 690–761 | Split by district / content type | **M** |
| P3 | Theme/preferences sync | — | Single theme SoR | **S** |
| P3 | Favorites/recents unification | — | One API for shell + palette | **M** |

---

## 3. Components recommended to split

| Component / file | Suggested boundaries | Complexity |
|------------------|----------------------|------------|
| **App.tsx** | `lazyPages.ts` + `routes/{auth,dashboard,workspace,platformBuilder,runtime,identity}Routes.tsx` | **L** |
| **EnterpriseCityPage** | Header, viewport/plane, district panels, `useCityPan` / `useCityWheel` | **L** |
| **DashboardPage** | Mode switcher + Executive / Ops / Live shells as route sections | **M** |
| **FirstEntryPage** | One component per onboarding step + shared chrome | **M** |
| **AIProductionCenterPage** (~463) | Overview / studio / pipeline panels (partially done) | **M** |
| **AIBuilderStudioPage** (~556) | Catalog strip vs editor vs preview | **M** |
| **ControlCenterStudio / CollaborativeAIStudio / TeamMapStudio** | Studio canvas vs side panels vs toolbars | **M** |
| **TopNavigation** (~344, under threshold but dense) | Org/role/mode clusters as subcomponents | **S** |
| **FullLayout** | Optional: chrome strips registry loaded by route family | **M** |

---

## 4. Dead code that can be safely removed

> Verify with full-repo grep + test suite before deletion. **SAFE REMOVE** = no production importers found in this audit.

| Item | Path | Evidence | Risk | Complexity |
|------|------|----------|------|------------|
| **`useNavStore`** | `src/navigation/navStore.ts` | Zero external imports | **SAFE REMOVE** | **S** |
| **Legacy `CommandPalette`** | `navigation/components/CommandPalette.tsx` (+ possibly `navigation/managers/commandPalette.ts` if unused) | App mounts only `UniversalCommandPalette` | **SAFE REMOVE** after export cleanup | **S** |
| **`AuthLayout`** | `src/layouts/AuthLayout.tsx` | No imports found | **SAFE REMOVE** | **S** |
| **`shellNavFromCatalog`** | `modules/moduleCatalog.ts` | Exported; no callers | **SAFE REMOVE** | **S** |
| **`legacyCatalogLookup` / `legacyDirectExecute`** | `command-center/managers/security.ts` | `@deprecated`; unused | **SAFE REMOVE** | **S** |
| **`DashboardLayout` alias** | `layouts/DashboardLayout.tsx` | Thin FullLayout wrapper; replace imports with `WorkspaceLayout`/`FullLayout` | Safe after mass replace | **S** |
| **`ENTERPRISE_RU_SIDEBAR` as live nav** | `enterpriseRuNav.ts` | Sidebar uses intelligent groups; sidebar array **tests-only** | Deprecate → migrate tests → remove | **M** |
| **Console `AdminShell`** | `platform_console/.../AdminShell.tsx` | Marked deprecated | If unreferenced — remove | **S** |

### Not fully dead (do not remove yet)

| Item | Why keep |
|------|----------|
| `simpleModeNav.ts` | Still used by `quickActionSections.ts` |
| `menuEngine` / `navigationManager` | WebCore + NavigationDashboard + tests |
| `EnterpriseTwinPage` | Mounted via DigitalTwin wrapper |
| Route `Navigate` aliases | Bookmark / deep-link compatibility |
| `OWNER_RU_NAV` | Still imported by intelligent nav groups |

---

## 5. Suggested architecture improvements

### A. Canonical navigation (P0)

**Target:** One nav source of truth.

- **Canonical:** `ux-revolution/intelligentNavGroups` + `groupsForMode` + accordion store  
- **Metadata only:** `enterpriseRuNav` (roles, org options, owner items)  
- **Demote:** `menuEngine` → admin/debug or merge permission filtering into intelligent groups  
- **Remove:** flat `ENTERPRISE_RU_SIDEBAR` from product paths  

**Complexity:** **L** · Risk: medium (permission regressions)

### B. Canonical app context (P0)

**Target:** Single shared context API for pages.

- Prefer **`useSharedContext` / Integration Hub** as SoR (already route-synced)  
- Slim **WebCoreProvider** to theme/auth helpers only, or merge into Hub  
- Keep **LiveDashboardDataProvider** scoped to live dashboard subtree  

**Complexity:** **L** · Risk: medium (vertical workflow pages use `useWebCore`)

### C. Route modularization (P0)

**Target:** `App.tsx` &lt; 150 lines.

- Extract `legacyRouteAliases.ts` (all redirects)  
- Domain route modules + shared `lazyPages` registry  
- Document Hub vs dedicated path policy per module  

**Complexity:** **L** · Risk: low if behavior preserved

### D. Store hygiene (P1)

1. Delete dead `navStore`  
2. Single favorites/recents API (shell preferences)  
3. Theme only in `themeStore`; preferences store references it  
4. Document: `workspaceStore` = tenant context · `workspaceManager` = tabs · `desktopStore` = windows  

**Complexity:** **M** · Risk: low–medium

### E. Command system graph (P1)

Break cycle:

```
command-center managers ←→ commandRuntime
```

Extract shared catalog/types to `command-center-runtime/` or `shared/commands/`.

**Complexity:** **M** · Risk: medium

### F. Chrome provider merge (P2)

Merge CommandCenter + Navigation UI state into one `ShellChromeProvider` (palette, omnibox, quick switcher, hotkeys). Deduplicate ⌘K on `/desktop` (`CommandCenterProvider` + `useDesktopKeyboard`).

**Complexity:** **M** · Risk: low

### G. Runtime teardown (P2)

On logout / HMR dispose: stop `runtimeEngine` / `healthService` intervals and `enterpriseShellRuntime` bus subscription. Today they are session singletons (acceptable but leaky under hot reload).

**Complexity:** **M** · Risk: low

### H. Cross-app strategy (P3)

Decide: `platform_console` stays standalone operator app **or** embeds into `src/web` operator mode. Until then, share only contracts (health DTO, auth), not UI.

**Complexity:** **L** · Risk: product decision

### I. Oversized surface split (P2–P3)

City, Desktop store, Production store, Dashboard, First Entry, builder wizards — split for testability and render isolation (complements 33.2.1 stability work).

**Complexity:** **L** (spread across sprints)

---

## 6. Estimated complexity matrix (all recommendations)

| ID | Recommendation | Severity | Complexity | Safe without product change? |
|----|----------------|----------|------------|------------------------------|
| R1 | Split `App.tsx` into route modules | High | **L** | Yes |
| R2 | Intelligent nav canonical; demote menuEngine | High | **L** | Mostly (test migrations) |
| R3 | Unify WebCore → Integration Hub | High | **L** | Yes if API shim kept |
| R4 | Delete `navStore`, legacy CommandPalette, AuthLayout | Med | **S** | Yes |
| R5 | Remove/replace `DashboardLayout` alias | Low | **S** | Yes |
| R6 | Unify favorites + recents | Med | **M** | Yes |
| R7 | Theme single SoR | Med | **S** | Yes |
| R8 | Break commandRuntime ↔ command-center cycle | Med | **M** | Yes |
| R9 | Merge chrome providers; fix dual ⌘K | Med | **M** | Yes |
| R10 | Split EnterpriseCityPage | Med | **L** | Yes |
| R11 | Slice desktopStore / productionStore | Med | **L** / **M** | Yes |
| R12 | Split DashboardPage | Med | **M** | Yes |
| R13 | Centralize legacy redirects + city canonical path | Low–Med | **S** | Yes (keep redirects) |
| R14 | Runtime engine teardown on logout | Med | **M** | Yes |
| R15 | Deprecate ENTERPRISE_RU_SIDEBAR (tests migrate) | Med | **M** | Yes |
| R16 | Shared format utils (`src/web`) | Low | **M** | Yes |
| R17 | platform_console strategy | Med | **L** | Product call |
| R18 | Extract ErrorBoundary shared fallback | Low | **S** | Yes |
| R19 | Quick actions single registry | Med | **M** | Yes |
| R20 | Drop dead `shellNavFromCatalog` | Low | **S** | Yes |

---

## 7. Unnecessary rerenders / wrappers (architecture notes)

Already mitigated in **33.2.1** (shared context `useShallow`, store equality guards, provider memoization). Remaining architecture-level rerender risks:

| Risk | Location | Suggestion |
|------|----------|------------|
| FullLayout always mounts many chrome strips | `FullLayout.tsx` | Route-family lazy chrome |
| LiveDashboard provider rebuilds activity on tick | `LiveDashboardDataContext` | OK if scoped under dashboard only |
| WebCore rebuilds full menu tree every auth/ws change | `WebCoreProvider` | Remove if Sidebar ignores it |
| Dual keydown handlers | CommandCenter + Navigation (+ Desktop) | Single hotkey router |

---

## 8. Memory / listener / timer risks

| Finding | Severity | Complexity |
|---------|----------|------------|
| Most React `addEventListener` / intervals have cleanup | OK | — |
| `runtimeEngine` / `healthService` intervals survive after last subscriber | **Med** | **M** |
| `enterpriseShellRuntime` bus sub cleared only on `shutdown()` (rarely called) | **Med** | **M** |
| `ProductionProviderStrip` timeout without unmount guard | **Low** | **S** |
| Duplicate ⌘K on desktop (waste, not leak) | **Med** | **S** |

---

## 9. Circular imports

| Cycle | Severity | Fix complexity |
|-------|----------|----------------|
| `command-center` managers ↔ `src/runtime/commandRuntime` | **Med** | **M** |
| Wide barrels (`@/ux-revolution`, platform-builder pages) increase coupling | **Low** | Gradual |

---

## 10. Legacy navigation map

```
Production Sidebar ──► intelligentNavGroups / groupsForMode / accordion
TopNavigation ───────► enterpriseRuNav metadata + Simple/Pro + RoleWorkspace
WebCoreProvider ─────► menuEngine (English /workspace/*) — NOT used by Sidebar
/navigation page ────► legacy NavigationDashboard (menuEngine metrics)
```

---

## 11. Suggested refactor sprint order (future — do not start without approval)

1. **33.2.3 Debt cleanup (S):** dead stores/components, theme sync, DashboardLayout alias, shellNavFromCatalog  
2. **33.2.4 Routes (L):** split App.tsx + alias registry  
3. **33.2.5 Nav unification (L):** menuEngine demotion  
4. **33.2.6 Context unification (L):** WebCore → Hub  
5. **33.3+ Surface splits:** City, Desktop, Production, Dashboard  

---

## 12. Audit inventory snapshot

| Metric | Value |
|--------|-------|
| TS/TSX files (`src/web`) | ~881 |
| Approx LOC | ~112,127 |
| Zustand store modules | ~20 |
| Files &gt;400 lines | 30+ |
| Largest product file | `App.tsx` / `EnterpriseCityPage.tsx` |
| Confirmed dead store | `navStore` |
| Active command palette | `UniversalCommandPalette` only |
| Primary shell layout | `FullLayout` via `WorkspaceLayout` |

---

## 13. Out of scope / not changed

- No code modifications in this sprint  
- No UI redesign, API, backend, or route behavior changes  
- No automatic deletions  

**Deliverable:** this report only.

---

## Appendix A — Top oversized files (wc -l)

| Lines | Path |
|------:|------|
| 1447 | `src/App.tsx` |
| 999 | `src/enterprise-city/EnterpriseCityPage.tsx` |
| 915 | `src/enterprise-desktop/desktopStore.ts` |
| 761 | `src/enterprise-city/cityCatalog.ts` |
| 701 | `src/ai-production-studio/productionStore.ts` |
| 690 | `src/ai-production-studio/productionCatalog.ts` |
| 663 | `src/onboarding/FirstEntryPage.tsx` |
| 646 | `platform-builder/god-mode/ControlCenterStudio.tsx` |
| 608 | `platform-builder/collaborative-ai/CollaborativeAIStudio.tsx` |
| 594 | `platform-builder/concierge/ConciergeWizard.tsx` |
| 585 | `src/modules/moduleCatalog.ts` |
| 578 | `platform-builder/vertical/VerticalWizard.tsx` |
| 575 | `platform-builder/ai-builder/AIBuilderWizard.tsx` |
| 572 | `src/pages/DashboardPage.tsx` |
| 569 | `src/runtime/commandRuntime/commandRuntime.ts` |
| 556 | `src/ai-builder-studio/AIBuilderStudioPage.tsx` |

*(Vertical workflow data files 424–651 lines omitted from split priority — mostly declarative.)*

---

## Appendix B — Store inventory (`src/web`)

| Store | Status |
|-------|--------|
| `authStore` | Canonical |
| `themeStore` | Canonical theme |
| `preferencesStore` | Overlaps theme |
| `notificationStore` | Canonical |
| `workspaceStore` | Tenant context |
| `workspaceManagerStore` | Tabs |
| `integrationContextStore` | Aggregated SPA context |
| `shellPreferencesStore` | Favorites / pins / recents |
| `shellLayoutStore` | Docks |
| `liveDashboardStore` | Widget layouts |
| `desktopStore` | Window manager |
| `productionStore` | AI production |
| `experienceModeStore` / `navAccordionStore` | UX 33.1–33.2 |
| `roleSwitcherStore` / `orgSelectorStore` | Chrome |
| `lastModuleStore` | HomeRedirect |
| `firstEntryStore` | Onboarding |
| `academyStore` | Platform builder |
| **`navStore`** | **Dead** |
