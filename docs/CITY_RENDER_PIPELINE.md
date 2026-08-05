# City Render Pipeline

**Sprint:** CG-2
**Code:** `src/web/src/enterprise-city/graphics/layerSystem.ts`, `graphics/renderPipeline.ts`

## 1. Layer System

Eight independently-enabled render layers, fixed paint order:

| Order | Layer | Default |
|---|---|---|
| 0 | `background` | enabled |
| 1 | `roads` | enabled |
| 2 | `buildings` | enabled |
| 3 | `effects` | enabled |
| 4 | `agents` | enabled |
| 5 | `selection` | enabled |
| 6 | `ui_overlay` | enabled |
| 7 | `debug` | **disabled** |

A layer is a visibility/order record only (`LayerState = { id, label, order, enabled }`) — it owns no
DOM, no store, and no business logic. `createLayerRegistry(overrides?)` produces a **new, independent
registry per call**; there is deliberately no shared mutable singleton across screens, so two City
screens (or a screen and its own debug panel) can hold different layer states without stepping on each
other.

```ts
const registry = createLayerRegistry({ debug: true });
registry.isEnabled("buildings");   // true
registry.toggle("debug");          // returns a NEW registry — the original is untouched
registry.ordered();                // layers sorted by paint order
```

`QUALITY_DISABLED_LAYERS` maps `low → [effects, debug]` and `medium → [debug]` — the Render Pipeline
applies these as registry overrides so a Low-quality frame doesn't pay for effect-layer work by
default, while an explicit per-call override still wins (a debug tool can force `effects` back on even
at Low quality).

## 2. Render Pipeline

`createCityFrame(options?)` is the single orchestration point: it composes the Scene Graph, Layer
System, Camera Engine bounds, and Graphics Config into one `CityFrame` object a screen consumes.

```ts
type CityFrame = {
  scene: SceneNode;                 // City -> District -> Building [-> Floor -> Room -> Object]
  stats: Record<SceneNodeKind, number>;
  layers: LayerRegistry;
  settings: GraphicsSettings;
  viewport: CityViewport;
  bounds: { zoomMin: number; zoomMax: number; panLimit: number };
};
```

```ts
const frame = createCityFrame({ viewport: currentViewport, floorExtensions });
if (shouldRenderLayer(frame, "effects")) { /* paint effects layer */ }
```

This file contains **no rendering itself** — no DOM manipulation, no canvas, no CSS. It only assembles
the read-only data a consumer (`EnterpriseCityPage.tsx`, or any future City screen) uses to decide what
to paint and in what order. Building the scene graph is proportional to the real, small catalog (12
districts / 34 buildings) — no pagination, memoization, or virtualization was needed at this scale; see
`SPRINT_CG_2_RESULT.md` §5 for the measured cost.

## 3. Composition, not a new abstraction

`createCityFrame` does not introduce a new rendering model. Every field on `CityFrame` is produced by
an already-documented module: `buildSceneGraph`/`sceneGraphStats` (`CITY_GRAPHICS_ENGINE.md` §3),
`createLayerRegistry` (§1 above), `cameraBounds` (`CITY_CAMERA.md` §1), `readGraphicsSettings`
(`CITY_GRAPHICS_ENGINE.md` §6). The pipeline's only job is assembling those into one object per frame
request, so a screen makes one call instead of five.

## 4. Test coverage

`graphics.test.ts` → `describe("layer system")` and `describe("render pipeline")`: default layer order
and Debug-off default, non-mutating toggle, quality-tier layer disabling, explicit overrides winning
over quality defaults, and frame composition (`scene.kind === "city"`, real bounds, correct
`shouldRenderLayer` results).
