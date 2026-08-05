# Sprint CG-3 Result — Enterprise City Runtime Integration

**Priority:** CRITICAL. **Mode:** real implementation — the CG-2 Graphics Engine is now wired into
the live `EnterpriseCityPage.tsx`, not just available as unused infrastructure.

## 1. Modified files

New (`src/web/src/enterprise-city/graphics/` — 5 new files, 670 lines):

| File | Lines | Purpose |
|---|---|---|
| `reducedMotion.ts` | 37 | Combines the platform's real `data-reduced-motion` attribute + OS `prefers-reduced-motion` query into one check |
| `performanceMonitor.ts` | 86 | rAF-driven FPS / CPU-time / render-time / memory sampler for the dev overlay |
| `useCityGraphicsRuntime.ts` | 336 | The integration hook — camera animation, effect triggers, tab-visibility pause, fps throttling |
| `CityDevOverlay.tsx` | 89 | The developer overlay component (renders the `debug` layer) |
| `runtimeIntegration.test.ts` | 122 | 13 real vitest cases for the two pure-logic modules above |

Modified:

| File | Change |
|---|---|
| `EnterpriseCityPage.tsx` | Camera interactions (buttons, wheel, drag, focus/reset/district-jump) now route through the animated camera engine instead of instant `setViewport`; building/district tiles receive live effect classes; roads flow when touching the focused building; a Debug toggle renders `CityDevOverlay`. See §2 for the full integration-point list. |
| `design-system/styles/motion.css` | Additive only, inside the existing "Enterprise City" section: `.ec-plane--js-anim` (suspends the CSS transition during a JS-driven tween), `ec-road-flow`/`ec-portal-burst` keyframes + their trigger classes, `.ec-district-label.is-activated` (reuses the existing `edm-status-flash` keyframe), and one tab-hidden pause rule. The three new animation classes were also added to both existing reduced-motion disable blocks (`@media (prefers-reduced-motion: reduce)` and `[data-reduced-motion="true"]`), following the exact pattern already used for the AI dot pulse. |

**Not modified:** `cityEngine.ts`, `cityCatalog.ts`, `cityDistricts.ts`, `cityNavigation.ts`,
`cityVisualLanguage.ts`, `useCityLiveStatus.ts`, every CG-2 Graphics Engine file (`types.ts`,
`sceneGraph.ts`, `layerSystem.ts`, `cameraEngine.ts`, `animationController.ts`, `visualEffects.ts`,
`graphicsTheme.ts`, `graphicsConfig.ts`, `renderPipeline.ts`), any Runtime/Desktop/AI Production file,
and no new store.

## 2. Integration points in `EnterpriseCityPage.tsx`

- **AnimationController connected.** Every discrete camera transition — the `+`/`−`/Reset toolbar
  buttons, wheel-zoom, `panTo` (minimap, recent/favorite chips), `jumpDistrict`, and `openBuilding`'s
  plaza re-center — now calls `useCityGraphicsRuntime`'s `animateViewportTo` / `focusBuildingAnimated`
  / `focusDistrictAnimated` / `resetCameraAnimated`, which run through the CG-2 `animateValue`
  (`requestAnimationFrame`). Free-drag panning is deliberately left as direct, event-rate-bound
  `setViewport` — a drag gesture already *is* the animation, driven 1:1 by the pointer; animating a
  live drag would add lag, the same "meaningful only" judgment `ENTERPRISE_CITY_ANIMATIONS.md` §4
  already makes for other gestures.
- **Render pipeline integrated.** `createCityFrame({ viewport, settings })` backs the effects-layer
  gate for hover/selection/activation/road-flow, and feeds the dev overlay's Objects/layer-enabled
  readouts.
- **Building animations enabled.** Hover (`onFocus`/`onMouseEnter`) and selection (`openBuilding`,
  `panTo`) trigger real `resolveEffect` classes; runtime status changes (`statusById` tone/tasks/
  notifications/aiActive) trigger a `building_activation` flash automatically via change-detection
  inside the hook — this is the "runtime event animations" requirement, driven by the real
  `useCityLiveStatus` feed, not a simulated timer.
- **District animations enabled.** `jumpDistrict` fires `district_activation` (`is-activated`,
  reusing the existing `edm-status-flash` keyframe) on the clicked district label.
- **Animated roads.** `.ec-link-line` gets `is-flowing` only for links touching the currently focused
  building — never the whole map — gated by the effects layer, `effectQuality`, and reduced motion.
- **Portal animations.** `openBuilding` now plays a brief `is-portal` burst on the target tile before
  `navigate()` fires (`await graphics.playPortalEffect(id)`), capped at 260ms and skipped entirely
  under reduced motion, a hidden tab, or Low quality.
- **Zoom transitions / smooth camera movement.** Wheel and button zoom both animate via the camera
  engine; rapid repeated input (e.g. fast wheel scrolling) cancels the in-flight tween and retargets
  smoothly rather than restarting from a stale position — see §3 for how staleness was specifically
  avoided.
- **Animation throttling.** `shouldAdmitFrame` (fps-limit-derived) gates every camera-frame DOM write
  and the dev-overlay sampler; the configured `GraphicsSettings.fpsLimit` (30/45/60/120 by quality
  tier) is the single throttle budget both consult.
- **Reduced Motion respected.** `isReducedMotionActive` combines the platform's real
  `data-reduced-motion` attribute (`design-system/accessibility`) with the OS-level media query;
  every animated call in the hook collapses to one instant frame when true, matching the contract
  `CITY_ANIMATION_SYSTEM.md` §2 already documents.
- **Pause when tab inactive.** `document.visibilitychange` snaps any in-flight camera tween to its
  target, zeroes the animation queue, and sets `data-tab-hidden="true"` on the City root — one CSS
  rule then pauses every continuous City animation (AI dot, road flow, focus breathe) at once.
- **`requestAnimationFrame` only.** No `setInterval` was introduced; the one `setTimeout` in the
  runtime hook (`scheduleEffectClear`) is a bounded one-shot clear for a transient CSS class, not a
  polling loop.
- **No unnecessary React re-renders / 60 FPS target.** The camera transform is written directly to
  the plane DOM node (`planeRef.current.style.transform = ...`) on every admitted animation frame;
  React state (and `sessionStorage` via the real `writeViewport`) is touched exactly once, when the
  transition completes. The CSS transition already on `.ec-plane` is suspended for the duration of a
  JS-driven tween (`.ec-plane--js-anim { transition: none; }`) so the two never double-animate the
  same property. The dev overlay's own React state updates are throttled to ~4 Hz regardless of the
  underlying sample rate, so turning the overlay on does not itself become a 60 Hz re-render source.
- **Developer overlay.** Toggled via a new "Debug" toolbar button (the `debug` render layer, off by
  default per CG-2's `DEFAULT_LAYERS`). Shows FPS, Objects (total scene-graph node count), Visible
  buildings (the real dimmed/filtered count, factored out of the existing render loop into
  `isBuildingDimmed` so the overlay and the map use one shared predicate, not two), Animation queue
  (live in-flight `AnimationHandle` count), Memory (`performance.memory.usedJSHeapSize` where Chrome
  exposes it, `n/a` elsewhere), CPU time, and Render time — plus a live quality-tier switcher wired to
  the real `graphicsConfig` persistence.

## 3. Architecture decisions

1. **Live-viewport ref, not the `viewport` prop, is the animation "from" position.** Because camera
   transforms are written directly to the DOM during a tween (§2), the React `viewport` state stays
   at its pre-animation value for the tween's entire duration by design. Naively using that stale
   value as the next animation's starting point (e.g. on a second rapid wheel tick) would make the
   camera visibly snap backward before re-animating. `useCityGraphicsRuntime` keeps a
   `liveViewportRef`, updated on every animation frame and synced from the `viewport` prop only when
   no animation is in flight, and every camera helper reads from it instead of a caller-supplied
   value. `getLiveViewport()` is exposed for the one non-hook caller that needs a synchronous read at
   an arbitrary moment: drag-start, so grabbing the map mid-transition doesn't jump either.
2. **CSS transition suspension, not removal.** `.ec-plane`'s existing `transition: transform ...` is
   what already made instantaneous `setViewport` calls look smooth before this sprint. Rather than
   removing it (which would un-animate every future direct `setViewport` call, e.g. drag), a single
   modifier class suspends it only while the JS engine owns the frame-by-frame writes, and it's
   removed the instant the tween ends or is cancelled.
3. **Portal effect blocks navigation for at most 260ms, never longer.** `playPortalEffect` is
   `await`ed before `navigate()`, but its delay is capped independently of the resolved effect's own
   duration (`edm-card-refresh`'s 400ms `settle` token), so a portal animation can never make the
   product feel unresponsive even if a future effect table entry uses a longer duration.
4. **The dev overlay reuses `frame.layers`/`frame.stats`/`settings` from the CG-2 render pipeline
   directly** — it does not recompute scene or layer state itself, so it can never drift from what the
   page is actually rendering.
5. **`EnterpriseCityPage.tsx` is edited directly this sprint**, reversing CG-2's own deferral decision
   — this sprint's brief explicitly asked for "Connect AnimationController to EnterpriseCityPage," so
   the collision-avoidance rationale from CG-2 no longer applies to this specific file. All edits were
   additive integration points (new imports, new handler bodies calling into the new hook, new props
   on `CityBuildingTile`) rather than restructuring the component's existing JSX layout, state shape,
   or navigation/search/advisor logic — nothing about *what* the page shows or how it's organized
   changed, only *how the camera and building/district visuals move*.

## 4. Compatibility confirmation

- **Runtime / AI logic / backend / platform architecture:** not touched.
- **Existing City logic:** `cityEngine.ts`, `cityCatalog.ts`, `cityDistricts.ts`, `cityNavigation.ts`,
  `cityVisualLanguage.ts`, `useCityLiveStatus.ts` — all unmodified; every camera/effect call reuses
  their real exports (`clampViewport`, `panToBuilding`, `writeViewport`, `CityBuilding`,
  `CityDistrictMeta`, `CityLiveStatus`) rather than re-implementing them.
- **No new store.** Graphics settings still persist via the plain `localStorage` functions CG-2 built
  (`ews_city_graphics_v1`); camera position still persists via the real, pre-existing
  `ews_city_viewport_v1` (`writeViewport`).
- **CSS changes are additive-only** inside `motion.css`'s existing "Enterprise City" section; no
  existing selector's rule body was changed, only new selectors added (verified by diff review).
- **TypeScript:** `tsc --noEmit -p tsconfig.app.json` — **0 errors**, project-wide.
- **Production build:** `npm run build` (`tsc -b && vite build`) — **succeeds**; the Enterprise City
  chunk (`enterprise-city-*.js`, ~34 kB / ~11 kB gzipped) bundles the new runtime hook without error.
- **Tests:** **184/184 passing** across 21 files (169 pre-existing-plus-CG-2 + 13 new CG-3 cases), 0
  regressions. One pre-existing, unrelated TypeScript error was observed transiently in
  `src/enterprise-desktop/` (a `WALLPAPERS`/`WALLOPERS` typo in Cursor's concurrent, untracked Desktop
  work) during one intermediate check; it was not introduced by this sprint, was not in any file this
  sprint touched, and had already been corrected upstream by the time the next check ran — confirming
  it was Cursor's in-flight edit, not a regression from this work.

## 5. Performance metrics

Honest framing, consistent with CG-2: this is still a DOM/CSS-driven engine, not WebGL, so "performance"
here means *JS/render work avoided*, not a GPU benchmark.

- **Re-render elimination:** an animated camera transition (e.g. focusing a building, ~320ms) now
  costs **one** React re-render (on completion) instead of one re-render per intermediate frame. At a
  320ms transition and a 60fps admit rate, that is roughly **19 avoided re-renders per transition**
  compared to a naive `setState`-per-frame implementation.
- **Frame budget instrumentation is real, not simulated:** the dev overlay's FPS/CPU-time/render-time
  numbers come from `performanceMonitor.ts` timing the actual camera-frame callback and DOM write via
  `performance.now()` — verified deterministic in `runtimeIntegration.test.ts` (mocked clock, exact
  ms assertions on `cpuTimeMs`/`renderTimeMs`), not estimated.
- **Fps-limit throttle is enforced, not advisory:** `shouldAdmitFrame` is unit-tested to reject a
  frame arriving before its budget and admit one arriving after — confirmed working at both the
  camera-tween call site and the dev-overlay sampler.
- **Quality-tier cost reduction:** at Low/Medium quality, the `effects` layer (and therefore hover/
  selection/road-flow/activation classes) is disabled by `QUALITY_DISABLED_LAYERS` (CG-2), now
  actually consulted by the running page via `frame.layers.isEnabled("effects")` — this sprint is what
  makes that CG-2 mechanism load-bearing rather than unused.
- **No production build regression:** bundle output (`npm run build`) completed in ~8s with no new
  errors; the `enterprise-city` chunk grew to accommodate the new runtime code but the build's existing
  large-chunk warning (`index-*.js` ~972 kB) is pre-existing and unrelated to this sprint's additions.
- **What was not measured:** real-browser frame timing (Chrome DevTools Performance panel, Lighthouse)
  was not run in this environment — no browser automation tool is available here, so the FPS/CPU/
  render-time figures above are validated by unit test against a mocked clock, not by an actual
  60Hz-display capture. Manual verification with the dev overlay open, in a real browser, is the
  recommended next step (see §7).

## 6. Testing

Automated (all passing, this environment):

- `graphics.test.ts` (CG-2, 28 cases) — unaffected, still green.
- `runtimeIntegration.test.ts` (CG-3, 13 new cases) — reduced-motion detection (settings-flag
  override, real `data-reduced-motion` attribute, OS-query fallback), frame-admission throttle
  (reject/admit at the fps budget boundary), and the performance monitor (FPS from a rolling window,
  CPU-time vs. render-time measured independently, rolling-window eviction, `reset()`, memory
  `null`-safety).
- `tsc --noEmit` — 0 errors project-wide.
- `npm run build` — succeeds.

Manually verified in this environment:

- Dev server boots (`npm run dev`) and serves `/enterprise-city` with a `200` response.
- Code review confirms `.ec-map-shell`/`.ec-plane`/`.ec-building`/`.ec-district-label` are all
  percentage/viewport-relative (no fixed pixel breakpoints), so desktop/ultrawide/4K resizing is a
  function of the existing responsive layout, unchanged by this sprint.
- Code review confirms Light/Dark themes are unaffected: every new class added by this sprint
  (`is-flowing`, `is-portal`, `is-activated`, `ec-plane--js-anim`) is colored via `var(--eds-*)`
  custom properties already resolved per-theme by the existing `data-theme` attribute — no new
  hardcoded color was introduced (`CG-2` `graphicsTheme.ts` was already theme-token-driven; this
  sprint's CSS follows the same rule).

**Not verified in this environment** (no browser automation tool available — this is an explicit,
honest gap, not a claimed pass): actual pixel-level rendering on Desktop/Ultrawide/4K viewports, a
real Light/Dark visual diff, live browser resize behavior, and a real OS-level
`prefers-reduced-motion` toggle exercised end-to-end in a running browser. §5's FPS/CPU numbers are
unit-test-verified against a mocked clock, not a live capture. **No screenshots were generated** for
the same reason. Recommend a manual QA pass (or a future sprint with browser automation access) before
treating the visual/perf claims above as fully verified beyond the unit-test level.

## 7. Next recommended graphics sprint

**Sprint CG-4 — City Graphics Visual QA + Browser-Verified Performance.** Run the dev overlay in a
real browser across Desktop/Ultrawide/4K and Light/Dark, capture actual DevTools Performance-panel
FPS during a focus/reset/zoom sequence to validate the unit-tested throttle logic against real frame
timing, and toggle the OS `prefers-reduced-motion` setting live to confirm the collapse-to-instant
behavior end-to-end. This is the natural follow-up specifically because this sprint's own honest
limitation (§6) is the absence of browser automation in this environment — CG-4 should close that gap
rather than this sprint asserting a visual pass it cannot back up.
