# STEP 22 — Odessa 3D GLB parse optimization + progressive activation

## Shipped

- First-load profiler (fetch / arrayBuffer / parse / prep / attach / first render) with per-asset timings and KPIs
- Asset lifecycle separate from loader status: `QUEUED → FETCHING → PARSING → PARSED → PREPARING → READY → ACTIVE / HIDDEN / FAILED`
- Parsed GLB roots stay **off-scene** until `ProgressiveSceneActivator` attaches them
- Frame-budgeted activation on the existing demand RAF loop (~4–6 ms IDLE; 0 ms INTERACTING; 2 ms SETTLING)
- Camera/frustum/priority-tile activation order; camera moves re-sort pending work and **do not discard** parsed assets
- Boot phases: `BOOTSTRAP → INTERACTIVE → FILLING → READY` (city usable at INTERACTIVE)
- Heavy-class LIGHT / MEDIUM / HEAVY / EXTREME; at most one HEAVY/EXTREME attach per frame
- Manifest bounds cache for scheduling (no per-tick `Box3`)
- Safari-safe `requestIdleCallback` fallback (`setTimeout` 16 ms) for **noncritical** prep only
- Yield via `requestAnimationFrame` between GLTF parses so two files are not parsed in the same turn
- Material intern audit: untextured equivalents only; skip maps / water / non-black emissive / mismatched opacity-blending
- Debug overlay: Downloaded / Parsed / Active / MB / boot / current asset / FPS / first-load KPIs / worst 10 parses

Not modified: original GLBs, manifest IDs, geoTransform, 2D map, CityEntity IDs, Three.js architecture. STEP 23 was not started.

## First-load architecture

| | Before (STEP 21) | After (STEP 22) |
|---|---|---|
| Parse | Main thread, pump could start next parse immediately | Main thread still; **RAF yield** between parses |
| Attach | Every `status=loaded` root added the same frame (`group.add` + intern + Box3) | Parsed roots held off-scene; attach by budget + priority |
| Bounds | `Box3.setFromObject` on every attach and often on visibility | Manifest center cache; measure once only if missing |
| Usable city | Overlay until all 45 GLBs reported loaded | **INTERACTIVE** after first attached geometry |
| Interaction | IDLE / INTERACTING / SETTLING paused **new fetches** | Same, plus **activation budget 0** while INTERACTING |

## Asset lifecycle

`AssetStatus` remains `idle|queued|loading|loaded|failed|unloaded` so streaming does not re-fetch after parse.

`lifecycle` is the activation state. After GLTF parse: `status=loaded`, `lifecycle=parsed`, `object3D` has **no parent**. Activator: `preparing` (single traverse) → `ready` → `active` (parented under the layer group). Distance visibility may flip `active ↔ hidden` without disposing.

Discard before attach: `ProgressiveSceneActivator.discard` / `disposePending` disposes unparented graphs. Interned materials are not disposed while still referenced (`disposeObject3D` skips interned mats).

## Activation budget policy

| Runtime mode (STEP 21) | Budget | Notes |
|---|---|---|
| INTERACTING | **0 ms** | No attach bursts; camera stays responsive |
| SETTLING | **2 ms** | LIGHT/MEDIUM only; HEAVY/EXTREME wait for IDLE |
| IDLE, FPS ≥ 50 | **6.5 ms** | Modest increase |
| IDLE, default | **5.5 ms** | Target 4–6 ms |
| IDLE, FPS < 28 | **3 ms** | Guard |

First asset in a frame with budget > 0 is always allowed (`spent=0`) so a single EXTREME can still appear; a second HEAVY/EXTREME in the same frame is refused.

## Heavy-asset thresholds

| Class | Triangles | Fallback |
|---|---|---|
| LIGHT | < 100k | `sizeMb * 18000` if tris unknown |
| MEDIUM | 100k–500k | `layerId === "heavy"` floored to at least MEDIUM |
| HEAVY | 500k–1.5M | smaller attach batches (one per frame) |
| EXTREME | > 1.5M | one per frame, skipped during SETTLING |

Manifest `triangles` is sparse; many chunks classify MEDIUM from file size until real counts are measured at prep.

## Safari / MacBook

- No WebGPU; Three.js WebGL only
- `requestIdleCallback` used only for optional prep of already-parsed roots
- Fallback: `setTimeout(16)` with `timeRemaining: () => 2`
- `yieldToNextFrame` uses `requestAnimationFrame`, else `setTimeout(0)`
- No Chromium-only `performance.memory` / long-task observer required (parse ≥ 50 ms counted as long-task in the profiler)

## Instrumented timings (debug overlay)

Per asset: id, URL, MB, fetch ms, parse ms, attach ms, triangles, objects.

KPIs: time to manifest / first parse / first geometry / first render / INTERACTIVE / 50% active / READY; total and average parse ms; long-task count; worst 10.

Live numbers appear after a real browser load (Диагностика). They are not hardcoded here.

## Largest parse offenders (manifest size, expected)

Package: 45 assets, 382.4 MB. Worst by `size_mb` (likely longest `GLTF.parse`):

1. `HEAVY_BUILDING_CHUNK_01_02_SUB_01_01` — 24.83 MB
2. `HEAVY_BUILDING_CHUNK_00_02` — 24.73 MB
3. `HEAVY_BUILDING_CHUNK_01_02_SUB_00_01` — 23.52 MB
4. `TILE_04_00_REST_BATCH_01` — 22.84 MB (370k tris authored)
5. `TILE_04_01` — 22.60 MB
6. `HEAVY_BUILDING_CHUNK_01_01` — 18.38 MB
7. `HEAVY_BUILDING_CHUNK_02_02_SUB_00_01` — 17.79 MB
8. `TILE_03_00` — 15.67 MB
9. `HEAVY_BUILDING_CHUNK_01_02_SUB_01_00` — 13.97 MB
10. `HEAVY_BUILDING_CHUNK_01_02_SUB_00_00` — 13.16 MB

Priority tiles (`priorityAssets`) still enqueue first (water/rest batches, TILE_03_01).

## Files changed

New:

- `src/web/src/enterprise-city/odessa3d/assetLifecycle.ts`
- `src/web/src/enterprise-city/odessa3d/idleCallback.ts`
- `src/web/src/enterprise-city/odessa3d/assetBoundsCache.ts`
- `src/web/src/enterprise-city/odessa3d/scenePrep.ts`
- `src/web/src/enterprise-city/odessa3d/firstLoadProfiler.ts`
- `src/web/src/enterprise-city/odessa3d/progressiveActivator.ts`
- `src/web/src/enterprise-city/odessa3d/parseActivation.test.ts`
- `docs/STEP_22_ODESSA_3D_PARSE_ACTIVATION_RESULT.md`

Modified:

- `assetLoader.ts` — lifecycle + timings + RAF yield + intern-safe unload
- `assetRegistry.ts` — in-place `update` (same object identity)
- `odessaSceneController.ts` — ingest / budgeted attach / boot / KPIs
- `Odessa3DView.tsx` — compact boot badge; detailed counters in diagnostics
- `types.ts`, `materialIntern.ts`, `index.ts`, `runtimePerfState.test.ts`

## Tests

`npm test -- src/enterprise-city` → **113 passed** (10 files).

Coverage added:

- lifecycle transitions (legal / illegal)
- activation priority
- frame-budget scheduler (no two HEAVY in one frame; INTERACTING = 0)
- no duplicate ingest
- manifest bounds cache
- Safari idle fallback
- discard/dispose of pending roots
- 2D → 3D → 2D + activator cleanup
- 3D remount without duplicates
- material intern: textured / emissive / water / opacity

## Build

`npx vite build` → **PASS** (existing chunk-size warnings only).

## Remaining bottleneck

**`GLTFLoader.parse` is still synchronous on the main thread.** STEP 22 stops attaching 45 hierarchies in one frame and yields between parses, but a single 20+ MB GLB can still hitch for tens to hundreds of ms on Intel Safari. Workers/Offscreen parse would be STEP 23+ and must not break Three.js WebGL or shared materials.

Secondary: GPU upload of large geometries at first attach of EXTREME tiles; mitigated by one-heavy-per-frame and INTERACTING budget 0.
