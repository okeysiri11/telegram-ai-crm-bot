# Sprint 46.6 — Vertical Navigation Stabilization

Two independent stabilization tasks landed in this sprint on `develop`:

1. Backend: fix a test-isolation failure in `tests/test_vertical_nav_46_5.py` (30/30 required).
2. Frontend: diagnose and fix an urgent regression — "Maximum update depth exceeded" crash
   immediately after registration/onboarding completes and the app transitions into the
   authenticated workspace.

No commits were made. All work is in the working tree on `develop` per instructions.

---

## Part 1 — Backend: `test_switching_beauty_auto_agro_crypto_is_deterministic`

### Root cause

**Test-isolation / shared-event-loop defect, not a production bug.**

`database/engine.py` caches a single `AsyncEngine` in a module-level global (`_engine`), and
`database/session.py` caches a single `async_sessionmaker` (`_session_factory`). Both are created
lazily on first use and never reset. `pytest.ini` runs with `asyncio_mode = auto` and no
session-scoped event-loop override, so pytest-asyncio gives each async test function its own event
loop. SQLAlchemy's async connection pool creates internal `asyncio.Queue`/`Future` primitives bound
to whichever loop is running when the engine is first used; a later test in a *different* loop
reusing that cached engine raises `Future attached to a different loop`, and once the first loop is
closed, cleanup attempts raise `Event loop is closed`.

Trace confirmed by reading the code: `enter_persona_home` → `_enter_auto` →
`handle_auto_menu_request` (`auto_vertical_handlers.py:806`) → `_user_lang` →
`VerticalOnboardingEngineV1.get_language` → `get_session()` (the shared engine) — this call sits
**outside** the function's own `try/except` (which only wraps lines 808–826), so nothing local
catches it.

Only the `auto` vertical touches the database in this navigation path — `_enter_beauty`,
`_enter_agro`, `_enter_crypto`, `_enter_legal`, `_enter_travel` are pure in-memory/keyboard code
(verified by reading each). Two tests in the file exercise `auto` + `owner`:
`test_auto_owner_hub_exposes_insurance_leasing_credit` (runs first, succeeds — binds the engine to
its own loop) and `test_switching_beauty_auto_agro_crypto_is_deterministic` (runs later, in a fresh
loop — inherits the now-stale engine and fails). This test-order dependency is the fingerprint of a
cross-loop engine reuse bug, not a logic defect in navigation.

### Fix — smallest safe change, test-side only

Followed the codebase's existing convention (`tests/test_buy_car_flow.py`,
`tests/test_sell_car_flow.py`, which already patch `VerticalOnboardingEngineV1.get_language` with
`AsyncMock` rather than hitting Postgres) and applied it to the two `auto` + `owner` tests in
`tests/test_vertical_nav_46_5.py`:

```python
monkeypatch.setattr(
    "auto_vertical_handlers.VerticalOnboardingEngineV1.get_language",
    AsyncMock(return_value="ru"),
)
monkeypatch.setattr(
    "auto_vertical_handlers.can_access_automotive_ui",
    AsyncMock(return_value=True),
)
```

- `get_language` covers `_user_lang`, used by `handle_auto_menu_request` and `_open_auto_hub` — the
  exact failure point in the observed trace.
- `can_access_automotive_ui` returning `True` skips the exception-fallback branch (`_main_menu_for`),
  which also touches the database and would otherwise cascade the same cross-loop error.
- Both tests' assertions only inspect the **last** `reply_markup` `msg.answer` received, which comes
  from the unconditional `auto_vertical_hub_menu()` message `_enter_auto` sends *after* calling
  `handle_auto_menu_request` — a pure function with no DB dependency. Mocking these two DB calls does
  not weaken what is actually asserted (real hub-menu buttons, real persona/session state, real
  deterministic switching across beauty/auto/agro/crypto).

No production code changed. `database/engine.py` / `database/session.py` are correct for the
one-event-loop-per-process production case; this was purely a test-harness gap.

### Files changed (backend)

- `tests/test_vertical_nav_46_5.py` — added the two `monkeypatch.setattr` pairs above to
  `test_auto_owner_hub_exposes_insurance_leasing_credit` and
  `test_switching_beauty_auto_agro_crypto_is_deterministic`.

### Backend result

```
.venv/bin/python -m pytest tests/test_vertical_nav_46_5.py -q
..............................                                           [100%]
30 passed in 8.05s
```

**30/30 PASS.**

---

## Part 2 — Frontend: post-onboarding "Maximum update depth exceeded"

### Reproduction

Browser tooling was unavailable in this session, so the crash was reproduced deterministically
inside the existing Vitest + `@testing-library/react` infrastructure (the repo already has this
pattern — see `src/modules/renderLoop.smoke.test.tsx` and
`src/test/platformStability_33_2_1.test.tsx`). Rendering `FullLayout` (wrapping either
`VerticalWorkspacePage` for every vertical or a bare child) under `CommandCenterProvider` +
`NavigationProvider` reproduced `Error: Maximum update depth exceeded` on **every** route —
`/dashboard`, `/vertical/owner`, `/vertical/auto`, `/vertical/beauty`, `/vertical/agro`,
`/vertical/crypto` — not just the new Beauty vertical. Bisecting `FullLayout`'s direct children in
isolation (`Sidebar`, `LeftDock`, `ActivityPanel`, `BottomDock`, `WorkspaceQuickDock`,
`UnifiedToastStrip`, `QuickCreateButton`, `ViewModeRouteGuard` all passed) isolated the fault to
`TopNavigation`.

### Root cause

**Zustand selector returning a new array reference on every call → React
`useSyncExternalStore` infinite-update loop.** (This matches the hint in the mission's own
inspection list: "any selector returning unstable objects/arrays causing effects to retrigger.")

`TopNavigation` unconditionally renders `<UnifiedIntentBar compact ... />` (and
`VerticalDashboard`, rendered inside every `/vertical/:verticalId` page, renders a second,
non-compact instance). `UnifiedIntentBar.tsx` selected:

```ts
const recent = useUnifiedIntentStore((s) => s.recent(5));
```

and `unifiedIntentStore.ts` defines:

```ts
recent: (n = 5) => get().items.slice(0, n),
```

`Array.prototype.slice` returns a **brand-new array** on every invocation, even when `items` hasn't
changed. Zustand's `useStore` hook is built on React's `useSyncExternalStore`, which calls the
selector on every snapshot check and compares the result with `Object.is`. A selector that returns a
new reference every time never stabilizes: React concludes the store "changed" on every render,
schedules another render, calls the selector again, gets another new array, and repeats — until React
hits its nested-update ceiling and throws. The identical anti-pattern existed in
`TaskInboxPanel.tsx` (`s.byFilter(filter)`, using `Array.prototype.filter`), reachable the moment a
user opens the "История" (history) panel.

This explains why the crash was reported as happening "after registration/onboarding" without being
specific to any one vertical: `TopNavigation` is rendered by `FullLayout` on essentially every
authenticated route, so the very first authenticated screen after onboarding — regardless of which
vertical it lands on — hits it. `UnifiedIntentBar`/`unifiedIntentStore` are Sprint 46.4 additions;
nothing about the Sprint 46.6 vertical-navigation changes introduced the bug, but Sprint 46.6's
onboarding→workspace transition work is what exercised the first authenticated paint carefully enough
to surface it.

**Ruled out:** `verticalWorkspaceStore.ts`'s `ewp_vertical_workspace_v1` → `v2` localStorage
migration, `moduleContextNav.ts`, the vertical selector/`WorkspaceSwitcher`, `roleSwitcherStore`
("view-as"), and `viewModeStore` — all read/write their state with equality guards
(`if (get().x === next) return;`) and none call an array/object-returning method directly as a
selector. They are not the cause of this crash (though `viewModeCatalog.ts`'s client/manager route
allowlists not yet including `/vertical/*` or `/workspace/beauty` is a separate, real gap noted under
Remaining Technical Debt below — it did not reproduce as a loop and was left alone per "smallest safe
change").

### Fix — smallest safe change

Selected the stable `items` array from the store and derived the slice/filtered view locally with
`useMemo`, instead of calling an array-returning store method directly as the selector. The store's
`recent`/`byFilter` methods are unchanged (still usable imperatively via `.getState()`), so no public
API or persistence behavior changed.

`src/web/src/workspace-chrome/unified-intent/UnifiedIntentBar.tsx`:

```diff
- const recent = useUnifiedIntentStore((s) => s.recent(5));
+ const items = useUnifiedIntentStore((s) => s.items);
+ const recent = useMemo(() => items.slice(0, 5), [items]);
```

`src/web/src/workspace-chrome/unified-intent/TaskInboxPanel.tsx`:

```diff
- const items = useUnifiedIntentStore((s) => s.byFilter(filter));
+ const allItems = useUnifiedIntentStore((s) => s.items);
+ const items = useMemo(
+   () => useUnifiedIntentStore.getState().byFilter(filter),
+   [allItems, filter],
+ );
```

No arbitrary counters/timeouts were introduced, the `RouteErrorBoundary` was left untouched, no
persistence was disabled, and Sprint 46.6 navigation behavior (Beauty as its own vertical, Auto
insurance/leasing/credit, Agro buy/sell nav) is unaffected — verified by the regression tests below.

### Regression tests added

`src/web/src/vertical-workspace/sprint_46_6_onboarding_workspace_transition.test.tsx` (new):

- Clean registration → authenticated workspace renders without an infinite update loop, with the
  correct vertical state.
- Page refresh after registration preserves the active vertical via persisted storage (simulated via
  `vi.resetModules()` + re-import, matching how `loadId()` re-runs on a real reload).
- Beauty → Auto → Agro switching settles without a render loop and without state bleed between
  verticals.
- Stale localStorage migration does not loop and resets to the safe `owner` default.
- View-as (`viewMode` / role switcher / active vertical) never mutates the authenticated user session
  (`useAuthStore`) — extends the existing pattern from
  `src/web/src/ux-revolution/viewMode_41_1.test.ts`'s "setViewMode does not clear auth session" test.

Also fixed two **pre-existing failing** tests in the Sprint-46.6-authored
`src/web/src/vertical-workspace/verticalWorkspaceStore.test.ts`: they set localStorage keys via the
raw literal (`"ewp_vertical_workspace_v1"`) instead of through `wsKey()`. Vitest's jsdom environment
defaults to `http://localhost:3000`, and `WORKSPACE_PORT_SLOTS["3000"] = "owner"`, so the store
actually reads/writes the prefixed key `ews_ws_owner__ewp_vertical_workspace_v1` in this test
environment — the tests were silently writing to a key the store never read. Fixed by routing the
test's `localStorage.setItem`/`getItem` calls through `wsKey()`, the same helper the store itself
uses; this is squarely the "stale localStorage migration" coverage requested and was not a loop bug,
just an incorrect test fixture.

### Files changed (frontend)

- `src/web/src/workspace-chrome/unified-intent/UnifiedIntentBar.tsx` — fix.
- `src/web/src/workspace-chrome/unified-intent/TaskInboxPanel.tsx` — fix.
- `src/web/src/vertical-workspace/verticalWorkspaceStore.test.ts` — fixed pre-existing key-prefix
  test bug (new file, authored earlier in Sprint 46.6, not previously committed).
- `src/web/src/vertical-workspace/sprint_46_6_onboarding_workspace_transition.test.tsx` — new
  regression suite (9 test cases across both files, all new).

### Frontend test result

```
npm run test
 Test Files  7 failed | 68 passed (75)
      Tests  9 failed | 515 passed (524)
```

All 9 new/fixed test cases (in `sprint_46_6_onboarding_workspace_transition.test.tsx` and
`verticalWorkspaceStore.test.ts`) pass. The 9 remaining failures are **pre-existing and unrelated**
to Sprint 46.6 — confirmed by re-running the full suite before touching any frontend code (baseline
was 11 failed/508 passed; fixing the 2 `verticalWorkspaceStore.test.ts` cases moved it to
9 failed/515 passed, and the same 9 failures were present, byte-for-byte, in the pre-change baseline).
None of the 9 touch `vertical-workspace/`, `workspace-chrome/unified-intent/`, `onboarding/`, or
`layouts/`:

| File | Failing test | Cause |
|---|---|---|
| `src/closed-beta/closedBeta.test.ts` | role homes cover Owner/Admin/... | `homeRouteForRole("client")` returns `/dashboard`, test expects `/dashboards/client` |
| `src/command-center-runtime/commandCenterRuntime.test.ts` | 2 tests | palette section catalog drifted from test expectations (`developer` section, `dev_open_runtime`) |
| `src/modules/moduleCatalog.test.ts` | 2 tests | shell nav route list / module readiness catalog drifted |
| `src/test/foundation.test.ts` | ecosystem templates | template titles now localized to Russian, test still expects English |
| `src/ux/client_ux_41_3.test.ts` | dock layout persistence | `DOCK_LAYOUT_KEY` localStorage write not observed |
| `src/workspace-engine/workspaceEngine.test.ts` | dock layout persistence | same `DOCK_LAYOUT_KEY` issue |
| `src/ux-revolution/uxRevolution.test.ts` | enterprise role workspaces | `homeRouteForRole("ceo")` returns `/owner`, test expects it to contain `/dashboard` |

These should be triaged separately — several look like the same root cause (`DOCK_LAYOUT_KEY`
possibly has the identical `wsKey()` port-3000 issue fixed here for `verticalWorkspaceStore.test.ts`)
but are out of scope for this sprint's mandate ("fix only Sprint 46.6-related failures").

### Lint result

```
npm run lint
src/ai-command/ai_command_center.test.ts(2,30): error TS2591: Cannot find name 'node:fs'. ...
src/ai-command/ai_command_center.test.ts(3,25): error TS2591: Cannot find name 'node:path'. ...
src/ai-command/ai_command_center.test.ts(7,38): error TS2304: Cannot find name '__dirname'.
src/ai-command/AiCommandCenterPage.tsx(105,20): error TS2322: Type '"accent"' is not assignable ...
src/hercules/hercules_control_center.test.ts(2,30): error TS2591: Cannot find name 'node:fs'. ...
src/hercules/hercules_control_center.test.ts(3,25): error TS2591: Cannot find name 'node:path'. ...
src/hercules/hercules_control_center.test.ts(8,15): error TS2304: Cannot find name '__dirname'.
```

**Pre-existing and unrelated** — confirmed via `git log` / `git diff --stat` that
`src/ai-command/` and `src/hercules/` were last touched in the `cc426de8` checkpoint commit, not by
any change in this session. Missing Node type definitions and one `Badge` tone typing mismatch;
neither file was touched by Sprint 46.6 work.

### Build result

```
npm run build
```

Fails at the `tsc -b` step with the same 7 pre-existing errors listed above (`vite build` never runs,
since `tsc -b && vite build` short-circuits). This is a **pre-existing, unrelated** blocker — same
root cause as the lint failures, present before this session's changes.

---

## Remaining technical debt (noted, not fixed — out of scope for this sprint)

- `src/web/src/ux-revolution/viewModeCatalog.ts`'s `CLIENT_ROUTES`/`MANAGER_EXTRA` allowlists (used
  by `ViewModeRouteGuard`) were never updated for the Sprint 42.8 `/vertical/*` framework or the
  Sprint 46.6 standalone `/workspace/beauty` route. A user in `client`/`manager`/`company_admin` view
  mode visiting any `/vertical/*` route or `/workspace/beauty` gets soft-redirected to `/dashboard`.
  This did not reproduce as part of the render-loop crash (bare navigation, not a ping-pong), but is
  a real navigation gap worth its own sprint item.
- The pre-existing `DOCK_LAYOUT_KEY` persistence test failures (`client_ux_41_3.test.ts`,
  `workspaceEngine.test.ts`) look like they may share the exact `wsKey()`-vs-jsdom-port-3000 root
  cause fixed here for `verticalWorkspaceStore.test.ts` — worth a follow-up sweep across all
  `wsKey()`-based test fixtures, not just the two files touched this sprint.
- Root `tsc -b` (lint/build) is currently red on `develop` independent of this work
  (`src/ai-command/`, `src/hercules/`) — blocks a clean `npm run build` until addressed separately.
- `src/web/src/workspace-chrome/unified-intent/unifiedIntentStore.ts`'s `recent`/`byFilter` methods
  remain array-returning "getter-style" store methods; they're safe to call imperatively
  (`.getState().recent(5)`) but are a footgun if a future component selects them directly again. A
  larger follow-up could rename them to make that non-selector intent explicit, or add an
  `eslint`/`oxlint` rule banning array/object-returning method calls directly inside a store selector
  — out of scope for this stabilization pass.

---

## git diff --stat

```
 handlers.py                                        |  90 +++++-
 keyboards.py                                       |  73 +++++
 platform_registry/menus/__init__.py                |  34 ++-
 platform_registry/verticals/__init__.py            |  21 +-
 services/vertical_nav_service.py                   |  96 +++++--
 src/web/src/platform-registry/menuCatalog.ts       |   3 +-
 src/web/src/ux-revolution/moduleContextNav.ts      |  36 +++
 src/web/src/vertical-workspace/catalog.ts          |  70 ++++-
 .../sprint_42_8_vertical_workspaces.test.ts        |  33 +++
 .../vertical-workspace/verticalWorkspaceStore.ts   |  16 +-
 .../unified-intent/TaskInboxPanel.tsx              |  12 +-
 .../unified-intent/UnifiedIntentBar.tsx            |   8 +-
 tests/test_vertical_nav_46_5.py                    | 301 ++++++++++++++++++++-
 13 files changed, 756 insertions(+), 37 deletions(-)
```

`handlers.py`, `keyboards.py`, `platform_registry/*`, `services/vertical_nav_service.py`,
`src/web/src/platform-registry/menuCatalog.ts`, `src/web/src/ux-revolution/moduleContextNav.ts`,
`src/web/src/vertical-workspace/catalog.ts`,
`src/web/src/vertical-workspace/sprint_42_8_vertical_workspaces.test.ts`, and
`src/web/src/vertical-workspace/verticalWorkspaceStore.ts` were already modified in the working tree
from earlier Sprint 46.5/46.6 work before this session started and are unchanged by this session.
This session's changes are: `tests/test_vertical_nav_46_5.py` (backend fix),
`src/web/src/workspace-chrome/unified-intent/UnifiedIntentBar.tsx` (frontend fix),
`src/web/src/workspace-chrome/unified-intent/TaskInboxPanel.tsx` (frontend fix), plus the two new
untracked test files listed under `git status --short` below.

## git status --short

```
 M handlers.py
 M keyboards.py
 M platform_registry/menus/__init__.py
 M platform_registry/verticals/__init__.py
 M services/vertical_nav_service.py
 M src/web/src/platform-registry/menuCatalog.ts
 M src/web/src/ux-revolution/moduleContextNav.ts
 M src/web/src/vertical-workspace/catalog.ts
 M src/web/src/vertical-workspace/sprint_42_8_vertical_workspaces.test.ts
 M src/web/src/vertical-workspace/verticalWorkspaceStore.ts
 M src/web/src/workspace-chrome/unified-intent/TaskInboxPanel.tsx
 M src/web/src/workspace-chrome/unified-intent/UnifiedIntentBar.tsx
 M tests/test_vertical_nav_46_5.py
?? .claude/
?? docs/SPRINT_46_5_FINAL_REPORT.md
?? docs/SPRINT_46_6_VERTICAL_NAV_STABILIZATION_REPORT.md
?? src/web/src/vertical-workspace/sprint_46_6_onboarding_workspace_transition.test.tsx
?? src/web/src/vertical-workspace/verticalWorkspaceStore.test.ts
```

`.claude/` (`settings.json`, `settings.local.json`) is local Claude Code harness/permission
configuration created during this session by the user's `/permissions` commands — not part of the
application, not touched by any code change, left as-is.

## Sprint status

- Stayed on `develop` throughout; no commits, no pushes, no resets, no branch switches, no
  dependency upgrades.
- Backend: **30/30 PASS** (`tests/test_vertical_nav_46_5.py`).
- Frontend: root cause found, fixed, and covered by 9 new/fixed regression test cases, all passing.
  9 pre-existing, unrelated test failures and a pre-existing `tsc -b` (lint/build) breakage were
  identified, confirmed unrelated via `git log`, and left untouched per the "fix only Sprint
  46.6-related failures" instruction.
