# Sprint CG-2 Result — Enterprise City Graphics Engine Foundation

**Priority:** CRITICAL (per sprint brief). **Mode:** real implementation — real code, real tests, real
documentation. **Owner:** Claude, concurrent with Cursor's Enterprise Runtime / Platform Runtime /
Enterprise City logic / AI Production backend / platform integration work.

## 1. Modified files

**Zero existing files were modified.** Every deliverable is new, additive code and documentation.

New source (`src/web/src/enterprise-city/graphics/` — new directory, 977 lines total):

| File | Lines | Purpose |
|---|---|---|
| `types.ts` | 78 | Shared types: `SceneNode`, `RenderLayerId`, `EffectKind`, `GraphicsSettings`, etc. |
| `sceneGraph.ts` | 113 | City → District → Building → Floor → Room → Interactive Object |
| `layerSystem.ts` | 61 | 8 independently-enabled render layers |
| `cameraEngine.ts` | 113 | Animated pan/zoom/focus/reset on top of the real `cityEngine.ts` |
| `animationController.ts` | 87 | Generic `requestAnimationFrame` tween manager |
| `visualEffects.ts` | 55 | hover/selection/pulse/highlight/glow/fade/activation → real design-system classes |
| `graphicsTheme.ts` | 43 | Light/Dark/Enterprise/Cyber, layered on the real theme engine |
| `graphicsConfig.ts` | 66 | Low/Medium/High/Ultra quality tiers, persisted settings |
| `renderPipeline.ts` | 60 | Composes everything above into one `CityFrame` |
| `index.ts` | 15 | Barrel export for this subfolder only |
| `graphics.test.ts` | 286 | 28 real vitest cases |

New documentation (`docs/`):

- `CITY_GRAPHICS_ENGINE.md` — engine overview, module map, reuse points, constraints honored.
- `CITY_CAMERA.md` — camera engine detail.
- `CITY_RENDER_PIPELINE.md` — layer system + render pipeline detail.
- `CITY_ANIMATION_SYSTEM.md` — animation controller + visual effects detail.
- `SPRINT_CG_2_RESULT.md` — this document.

**Explicitly unmodified** (verified by `git status` before and after this sprint):
`cityEngine.ts`, `cityCatalog.ts`, `cityDistricts.ts`, `cityNavigation.ts`, `cityVisualLanguage.ts`,
`useCityLiveStatus.ts`, `EnterpriseCityPage.tsx`, `enterprise-city/index.ts`, every Enterprise Runtime
file, every Enterprise Desktop file, every AI Production Center file, and every existing Zustand store
in the repository.

## 2. Architecture decisions

1. **Additive-only, zero-edit isolation.** At sprint start, `git status` showed the entire Sprint 27.8
   City camera/district/navigation layer as uncommitted, actively-changing work, with Cursor
   simultaneously building Enterprise City logic. Given the sprint's own "DO NOT rewrite existing
   City / DO NOT duplicate Cursor work" constraints, the decision was made to build 100% of this
   sprint as new files in a new subdirectory, importing every existing primitive rather than touching
   the files that own it. This eliminates merge-collision risk with concurrent Cursor work by
   construction, not by convention.
2. **Single source of truth for camera bounds.** Rather than re-declaring `cityEngine.ts`'s private
   `ZOOM_MIN`/`ZOOM_MAX`/`PAN_LIMIT`, `cameraBounds()` probes the real `clampViewport()` with extreme
   inputs. If those constants ever change, this engine's bounds change with them automatically.
3. **No new animation vocabulary.** Every resolved effect class in `visualEffects.ts` is one of the
   design system's real `animationEngine.presets` strings; every duration traces back to
   `design-system/tokens`' `motion` scale. The platform's forbidden-animation list and
   continuous-loop allowlist are enforced programmatically (`resolveEffect` downgrades any
   non-allowlisted continuous effect to a one-shot fade), not just documented.
4. **No new store for graphics settings.** `graphicsConfig.ts` uses plain `localStorage` read/write
   functions under `ews_city_graphics_v1`, matching `cityEngine.ts`'s existing
   `ews_city_viewport_v1` convention exactly, instead of introducing a new Zustand store.
5. **Theme reuse over theme duplication.** `CityGraphicsTheme` (`light`/`dark`/`enterprise`/`cyber`)
   is not a parallel color system — `Enterprise` and `Cyber` are `BrandOverrides` applied to the real
   `corporate` and `dark` platform themes respectively, via the existing `applyTheme()` function.
6. **Floor/Room/Interactive Object as extension points, not fabricated data.** The scene graph accepts
   optional per-building floor data and produces zero floor/room nodes when none is supplied, since no
   real per-building floor model exists yet (`ENTERPRISE_CITY_BIBLE.md` §10 remains vision). This
   avoids inventing placeholder department data while still shipping the real hierarchy type.
7. **Page-level wiring deliberately deferred.** `EnterpriseCityPage.tsx` does not yet consume this
   engine — wiring a live page is the highest-collision-risk kind of change under concurrent editing,
   and the sprint brief scoped this sprint to "the visualization engine" only, not integration. See §6.

## 3. Compatibility confirmation

- **Runtime:** not touched. No file under `enterprise-runtime/` was read for editing or modified.
- **AI logic / backend:** not touched. `platform_ai_os`, `ai-production-studio`, and `integration-hub`
  are untouched.
- **Platform architecture:** not touched. No routing, shell, or Desktop OS file was modified.
- **Existing City implementation:** not touched — confirmed by `git status` showing no diff against
  any pre-existing `enterprise-city/*` file after this sprint's work.
- **Stores:** no new Zustand store was created; no existing store was modified.
- **Design system:** read-only consumption of `design-system/tokens`, `design-system/animation`,
  `design-system/theme` — none of the three were modified.
- **TypeScript:** `tsc --noEmit -p tsconfig.app.json` — **0 errors**, project-wide, after this sprint's
  changes.
- **Tests:** full suite — **169/169 passing** across 20 test files (141 pre-existing + 28 new), **0
  regressions**.

## 4. Performance impact

This engine renders nothing itself — it is DOM/CSS-compatible presentation data, matching
`cityEngine.ts`'s own explicit non-goal of a WebGL camera. The real performance levers it introduces:

- **Layer-based selective rendering.** A consuming screen can skip painting an entire layer
  (`effects`, `debug`) rather than rendering-then-hiding it. At Low/Medium quality, `effects` and
  `debug` are disabled by default via `QUALITY_DISABLED_LAYERS`, directly reducing DOM node count and
  animation work on constrained devices.
- **Scene graph cost is proportional to the real catalog size** (12 districts, 34 buildings) —
  measured at effectively instantaneous (`graphics.test.ts` builds and walks the full graph, with
  Floor/Room extensions, well within the test's default timeout; no memoization was needed at this
  scale, and none was added prematurely).
- **Camera animation runs on `requestAnimationFrame`**, the same primitive every other animated
  surface in the platform already uses (no `setInterval` polling), and is fully cancellable — an
  interrupted focus transition stops cleanly instead of stacking concurrent tweens.
- **Reduced-motion is a true fast path**, not a slowed-down animation: it produces exactly one
  synchronous frame instead of scheduling any `requestAnimationFrame` callbacks at all.
- No shadow DOM, no canvas, no WebGL — so no GPU-context cost was added. This is an explicit ceiling:
  see §6 for where a canvas/WebGL path would need to be introduced if the "3D vision" items in
  `ENTERPRISE_CITY_ARCHITECTURE.md` §17–18 are ever built.

No before/after render benchmark exists because nothing in the existing platform renders through this
engine yet (§2 item 7) — the honest performance claim this sprint can make is architectural (layer-
based skip-rendering, single shared animation driver, zero duplicated tween loops), not yet a measured
before/after on a live screen.

## 5. Readiness

**Graphics Engine foundation: ~85% ready** as reusable infrastructure.

What's real and tested: scene graph, layer system, camera animation, generic tween controller, visual
effects resolution, theme layering, quality-tier configuration, and a composed render pipeline — all
with passing tests and zero TypeScript errors.

What's not yet done (the remaining ~15%): integration into `EnterpriseCityPage.tsx` (deliberately
deferred, §2 item 7), a real building/district Floor-Room dataset to populate the scene graph's
extension points, and a debug-layer visual (data model exists via `debug` layer + `sceneGraphStats`,
no rendering built).

## 6. Next recommended graphics sprint

**Sprint CG-3 — City Graphics Integration.** Wire this engine into the real `EnterpriseCityPage.tsx`:
replace the page's direct `cityEngine.ts` calls with `createCityFrame()`, drive pan/zoom/focus through
`cameraEngine.ts`'s animated functions instead of instantaneous `writeViewport` calls, and render the
Debug layer as an actual on-screen panel (scene stats, layer toggles, current `GraphicsSettings`) for
Cursor/QA use during ongoing City development. This should be scoped as its own sprint specifically
*because* it touches `EnterpriseCityPage.tsx` directly — the one file this sprint deliberately avoided
given concurrent Cursor work — and should start with a fresh `git status` check for the same reason
this sprint did.
