# STEP 21 — Odessa 3D Performance + Smooth Camera Runtime

## Shipped

- Runtime modes **IDLE / INTERACTING / SETTLING** (`runtimePerfState.ts`)
- Interaction-aware rendering: pause new GLB loads while orbiting/panning/zooming; in-flight loads continue
- Restore streaming after ~320 ms idle; SETTLING uses 1 concurrent load
- AUTO FPS guard: step DPR down if avg FPS stays below ~27 for 3.5 s; recover only after FPS > 42 for 8 s
- Pixel-ratio policy: never use full `devicePixelRatio` above 1.5; AUTO starts at 1.0
- Camera: damping 0.085, rotate 0.58, zoom 0.82; close-range pan + `zoomToCursor` kept; target not reset on pan
- Distance visibility skipped while INTERACTING (no pop-out while orbiting)
- Cached asset centers (no per-tick `Box3.setFromObject` scan)
- Safe untextured material intern across tiles (Water excluded; interned mats not disposed on heavy unload)
- Dev **Диагностика** overlay: FPS, frame ms, draw calls, triangles, geometries, textures, loaded/visible/queued assets, camera distance, pixel ratio, runtime mode, stream paused

## Files changed

- `src/web/src/enterprise-city/odessa3d/runtimePerfState.ts` (new)
- `src/web/src/enterprise-city/odessa3d/runtimePerfState.test.ts` (new)
- `src/web/src/enterprise-city/odessa3d/materialIntern.ts` (new)
- `src/web/src/enterprise-city/odessa3d/odessaPerformance.ts`
- `src/web/src/enterprise-city/odessa3d/odessaPerformance.test.ts`
- `src/web/src/enterprise-city/odessa3d/qualityProfile.ts`
- `src/web/src/enterprise-city/odessa3d/assetLoader.ts`
- `src/web/src/enterprise-city/odessa3d/tileStreaming.ts`
- `src/web/src/enterprise-city/odessa3d/odessaSceneController.ts`
- `src/web/src/enterprise-city/odessa3d/cameraNavigation.ts`
- `src/web/src/enterprise-city/odessa3d/cameraNavigation.test.ts`
- `src/web/src/enterprise-city/odessa3d/disposeUtils.ts`
- `src/web/src/enterprise-city/odessa3d/types.ts`
- `src/web/src/enterprise-city/odessa3d/Odessa3DView.tsx`
- `src/web/src/enterprise-city/odessa3d/index.ts`
- `docs/STEP_21_ODESSA_3D_RUNTIME_PERF_RESULT.md`

Not modified: GLBs, manifest, geoTransform, 2D map, entity IDs, Blender sources.

## Renderer settings

| | Before | After |
|---|---|---|
| antialias AUTO | medium=true | **false** (explicit HIGH still true) |
| pixelRatio AUTO start | cap 1.5 at highest step | **1.0**, cap 1.25 desktop / 1.0 low-power |
| pixelRatio MEDIUM | 1.25 | **1.0** |
| pixelRatio HIGH | min(dpr, 1.5) | same, hard cap 1.5 |
| shadows | off | off |
| logarithmicDepthBuffer | off | **off** |
| powerPreference | high-performance | same |
| tone mapping | ACES 1.05 | same |
| dampingFactor | 0.06 | **0.085** |
| rotateSpeed | 0.65 | **0.58** |
| zoomSpeed | 0.9 | **0.82** |
| zoomToCursor | true | true |
| screenSpacePanning | true | true |
| stream while moving | schedule every 500 ms | **paused INTERACTING** |
| FPS guard trip | frameMs > 22 (~45 fps) | **FPS < 27 for 3.5 s** |

## AUTO quality behavior

- Low-power (narrow viewport or ≤4 cores): LOW distances, concurrent 1, DPR cap 1.0, no antialias, no shadows
- Desktop AUTO: medium distances, concurrent 2, DPR cap 1.25, starts at 1.0, no antialias
- Never applies devicePixelRatio > 1.5

## Pixel ratio policy

Steps: `0.75 → 1.0 → 1.25 → 1.5`. AUTO starts at 1.0. While INTERACTING, dip at most −0.25 and never below 1.0 (no visible smear). LOW 0.75–1.0 via FPS guard only in AUTO.

## Streaming concurrency policy

- IDLE: quality `maxConcurrentLoads` (1–3), reduced to 1 if AUTO DPR degraded to 0.75
- INTERACTING: new loads paused; in-flight continue; already loaded tiles kept
- SETTLING (~320 ms): resume with 1 concurrent, no heavy unload
- Priority still camera-target / frustum / view-direction via existing `scoreTilePriority`

## Camera interaction

- Damping on; no target reset during pan
- Distance-aware pan from STEP 20 unchanged
- `zoomToCursor` unchanged
- Pan-speed updates throttled (distance delta ≥ 4 m)

## FPS guard

- Poor: avg FPS < 27 for 3.5 s → one DPR step down (+ tighter stream cap)
- Recover: avg FPS > 42 for 8 s → one step up
- Dead band 27–42: no change (no oscillation)

## Test / build

- `npm test -- src/enterprise-city` — **96 passed** (9 files)
- `npx vite build` — **PASS** (14.80s). Pre-existing chunk-size warnings only.

## Manual verification

http://localhost:5180/enterprise-city → **3D Одесса** → wait for ODESSA READY → orbit / close pan / rapid zoom. Debug overlay: **Диагностика**.

## Remaining bottleneck

- 45 GLBs / large triangle counts still dominate first-load hitch; parse remains on main thread (workers deferred)
- Distant city tiles stay resident by STEP 18 invariant (only `heavy` unloads)
- Material intern is untextured-only; textured buildings still duplicate GPU programs per GLB

## Deferred

- STEP 22
- Worker GLB parse
