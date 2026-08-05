# City Graphics Engine

**Sprint:** CG-2 — Enterprise City Graphics Engine Foundation
**Status:** real implementation, additive only.
**Code:** `src/web/src/enterprise-city/graphics/` (new directory; zero existing City files modified)
**Scope:** visualization foundation only — no business logic, no Runtime, no backend, no API.

This document is the entry point for the four CG-2 documents. It does not repeat
`CITY_ENGINE.md` (the real camera/viewport primitives from Sprint 27.8) or
`ENTERPRISE_CITY_ANIMATIONS.md` (the platform's animation *specification*) — it describes the new
*engine* code that implements against those specs, and links out to the companion documents for
camera, render-pipeline, and animation detail.

## 0. Why this exists

Sprint 27.8 gave Enterprise City a real camera (`cityEngine.ts`), a real district/building catalog
(`cityCatalog.ts`, `cityDistricts.ts`), and real navigation state (`cityNavigation.ts`). None of that
is a *graphics engine* — there was no shared scene hierarchy, no layer system, no reusable
animation/effect vocabulary, and no quality-tier configuration. Every future City screen (department
drill-down, floor/room views, multiplayer presence, the "3D vision" items in
`ENTERPRISE_CITY_ARCHITECTURE.md` §17–18) would otherwise reinvent this machinery per screen. CG-2
builds it once, as infrastructure, on top of the real primitives that already exist.

## 1. Hard constraints this sprint honored

At the time this sprint started, `git status` showed the entire Sprint 27.8 camera/district/
navigation layer as **uncommitted, in-progress work** (several files fully untracked, others with
1000+ uncommitted line changes), with Cursor simultaneously implementing Runtime, Platform Runtime,
City logic, and AI Production backend. Given that, and the sprint's explicit "DO NOT rewrite existing
City / DO NOT duplicate Cursor work / DO NOT create duplicate stores" constraints, every module in
this engine was built as **new, additive code with zero edits to any existing Enterprise City file**:

- `cityEngine.ts`, `cityCatalog.ts`, `cityDistricts.ts`, `cityNavigation.ts`,
  `cityVisualLanguage.ts`, `useCityLiveStatus.ts`, `EnterpriseCityPage.tsx`, and
  `enterprise-city/index.ts` are all **unmodified**.
- The new code lives entirely under `enterprise-city/graphics/`, its own subdirectory with its own
  barrel export (`graphics/index.ts`) — the existing `enterprise-city/index.ts` does not import from
  or re-export it.
- Every primitive that already existed for real (viewport clamping, `panToBuilding`, building/district
  catalogs) is **imported and reused**, never re-declared. See §4 for the specific reuse points.
- Page-level wiring (making `EnterpriseCityPage.tsx` actually consume this engine) is explicitly **out
  of scope** for this sprint and left as the first recommended follow-up (`SPRINT_CG_2_RESULT.md`
  §6) — wiring a page is exactly the kind of change that could collide with concurrent Cursor edits to
  that same file, whereas a new, unimported directory cannot.

## 2. Module map

| Module | File | Responsibility |
|---|---|---|
| Types | `graphics/types.ts` | Shared types every other module depends on: `SceneNode`, `RenderLayerId`, `EffectKind`, `ResolvedEffect`, `GraphicsQuality`, `GraphicsSettings`, `CityGraphicsTheme`, `AnimationHandle`. |
| Scene Graph | `graphics/sceneGraph.ts` | Builds City → District → Building → Floor → Room → Interactive Object tree from the real catalogs. See §3. |
| Layer System | `graphics/layerSystem.ts` | 8 independently-enabled render layers. See `CITY_RENDER_PIPELINE.md` §1. |
| Camera Engine | `graphics/cameraEngine.ts` | Pan/zoom/focus/reset **animation** layered on the real `cityEngine.ts` camera. See `CITY_CAMERA.md`. |
| Animation Controller | `graphics/animationController.ts` | Generic `requestAnimationFrame` tween manager. See `CITY_ANIMATION_SYSTEM.md`. |
| Visual Effects | `graphics/visualEffects.ts` | Resolves hover/selection/pulse/highlight/glow/fade/activation effects to real design-system classes. See `CITY_ANIMATION_SYSTEM.md` §3. |
| Theme Engine | `graphics/graphicsTheme.ts` | Light/Dark/Enterprise/Cyber City themes, layered on the real `design-system/theme`. See §5. |
| Graphics Config | `graphics/graphicsConfig.ts` | Low/Medium/High/Ultra quality tiers, FPS limit, per-category quality, persisted settings. See §6. |
| Render Pipeline | `graphics/renderPipeline.ts` | Composes all of the above into one `CityFrame` a screen consumes. See `CITY_RENDER_PIPELINE.md`. |
| Tests | `graphics/graphics.test.ts` | 28 vitest cases, pure-logic style (matches `cityCore.test.ts` / `desktopStore.test.ts` conventions — no component rendering). |

## 3. Scene Graph

`buildSceneGraph(floorExtensions?)` builds the hierarchy directly from the **live** catalogs —
`CITY_DISTRICTS` (12 real districts) and `CITY_BUILDINGS` (34 real buildings, plaza excluded from
district children since it renders separately). City → District → Building is real data today.
Floor → Room → Interactive Object are typed **extension points**
(`SceneFloorExtension`/`SceneRoomExtension`), not fabricated data — no per-building floor/room model
exists in the platform yet (`ENTERPRISE_CITY_BIBLE.md` §10, "Departments," remains vision). Passing
real floor data in activates those levels automatically with zero change to this module.

One traversal (`walkSceneGraph`), one lookup (`findSceneNode`), one stats function
(`sceneGraphStats`) — every layer/debug overlay that needs to inspect the tree shares these instead
of writing its own walk.

## 4. Reuse points (what was *not* duplicated)

| Existing real primitive | Owner file | Reused by |
|---|---|---|
| `CityViewport`, `clampViewport`, `DEFAULT_VIEWPORT`, `panToBuilding` | `cityEngine.ts` | `cameraEngine.ts` — imported directly, never re-declared |
| `ZOOM_MIN` / `ZOOM_MAX` / `PAN_LIMIT` (private) | `cityEngine.ts` | `cameraEngine.ts`'s `cameraBounds()` **probes** the real `clampViewport` with extreme inputs to derive bounds, rather than re-declaring the private constants a second time |
| `CITY_BUILDINGS`, `CityBuilding`, `CityBuildingId` | `cityCatalog.ts` | `sceneGraph.ts`, `cameraEngine.ts` |
| `CITY_DISTRICTS`, `CityDistrictMeta` | `cityDistricts.ts` | `sceneGraph.ts`, `cameraEngine.ts` |
| `motion` tokens (durations, easings) | `design-system/tokens` | `animationController.ts` |
| `animationEngine` presets + forbidden/continuous-loop rules | `design-system/animation` | `visualEffects.ts` |
| `ThemeId`, `BrandOverrides`, `applyTheme` | `design-system/theme` | `graphicsTheme.ts` |

No new Zustand store, no new camera, no new desktop/window system, no new color palette, and no
duplicated animation vocabulary were created.

## 5. Theme Engine

City themes (`"light" | "dark" | "enterprise" | "cyber"`) are skins layered on the platform's real
`ThemeId` (`"light" | "dark" | "corporate" | "custom"`) — `applyCityGraphicsTheme()` delegates to the
real `applyTheme()`. `Light`/`Dark` map straight through. `Enterprise` rides on `corporate` with a
brand accent; `Cyber` rides on `dark` with a brand accent — both via the existing `BrandOverrides`
mechanism (the same one any tenant brand override already uses), never a second color system. Future
City themes register in one lookup table (`CITY_THEMES`) without touching `applyCityGraphicsTheme`'s
logic.

## 6. Graphics Configuration

`GraphicsSettings` covers `quality` (Low/Medium/High/Ultra), `fpsLimit`, and independent
`animationQuality`/`effectQuality`/`shadowQuality`/`iconDensity`, each itself a quality tier. Persisted
via plain `localStorage` read/write functions (`readGraphicsSettings`/`writeGraphicsSettings`) under
the key `ews_city_graphics_v1` — following the exact naming convention `cityEngine.ts` already uses
for `ews_city_viewport_v1`, and deliberately **not** a new Zustand store. `normalizeGraphicsSettings`
repairs a corrupt/partial persisted value field-by-field rather than discarding it wholesale. The
Layer System consults `QUALITY_DISABLED_LAYERS` so Low/Medium quality disable the `effects`/`debug`
layers by default (overridable per-frame).

## 7. Companion documents

- [`CITY_CAMERA.md`](./CITY_CAMERA.md) — camera engine detail (pan/zoom/focus/reset animation, bounds).
- [`CITY_RENDER_PIPELINE.md`](./CITY_RENDER_PIPELINE.md) — layer system + render pipeline detail.
- [`CITY_ANIMATION_SYSTEM.md`](./CITY_ANIMATION_SYSTEM.md) — animation controller + visual effects detail.
- [`SPRINT_CG_2_RESULT.md`](./SPRINT_CG_2_RESULT.md) — sprint report: files touched, architecture
  decisions, compatibility confirmation, performance impact, readiness, next sprint.
