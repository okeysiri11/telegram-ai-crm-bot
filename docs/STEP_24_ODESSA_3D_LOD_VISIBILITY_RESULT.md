# STEP 24 — Odessa 3D LOD + visibility manager

## Shipped

Virtual LOD (no extra meshes). Distance tiers, hysteresis, screen-space importance, frustum/target/sea protection, starvation boost, and the same priority used by the streamer and STEP 22 activator.

STEP 20–23 preserved: water duplicate guard, IDLE/INTERACTING/SETTLING, frame-budgeted activation, environment/sky/fog.

Not done: fake `_lodN` GLBs, worker parse, weather, traffic, night lights, postprocessing, STEP 25.

## Architecture

```
odessa3d/lod/
  lodTypes.ts          DistanceTier, diagnostics
  lodThresholds.ts     quality-scaled near/mid/far
  lodScore.ts          priority formula, sea protect, URL policy
  lodVisibility.ts     hysteresis + hide policy
  lodManager.ts        evaluate 45 assets from bounds cache
```

`LodVisibilityManager` replaces the STEP 21 hard distance hide (`visibilityWithHysteresis` on every asset). City-layer tiles stay visible once active. Only **heavy** FAR/CULL tiles may hide, and only with hysteresis.

Streamer (`tileStreaming.ts`) scores tiles with `scoreLodPriority`. Heavy unload also requires beyond `farM`, not sea-protected, and not inside the look-at protect radius.

Activator (`progressiveActivator.ts`) uses the same score, plus wait-time starvation boost.

## Distance thresholds

Reference city diagonal 1400 m. `lodBias` from quality (LOW=2, MEDIUM=1, HIGH=0) shrinks bands.

| | NEAR | MID | FAR | CULL |
|---|---|---|---|---|
| HIGH (bias 0) | ≤ 420 m | ≤ 1050 m | ≤ 2400 m | beyond |
| MEDIUM (bias 1) | ~328 m | ~905 m | ~2222 m | beyond |
| LOW (bias 2) | ~269 m | ~795 m | ~2069 m | beyond |

Hysteresis **18%**: demote only after outer band, promote only after inner band. Target protect ~380 m × (diagonal/1400). Screen-important if projected radius ≥ 8% of view height.

## Priority formula (lower first)

```
score = distanceM
      - 8000  if sea/coast protected
      - 5000  if manifest priority
      - 2800  if near look-at
      - 2000  if in frustum
      - 1500  if screen-important
      - starveBoost(waitMs)     // min(420, waitMs/48)
      - 500 * max(0, forwardDot)
      + 700   if heavy layer / HEAVY
      + 1200  if EXTREME
      + 35 * max(0, sizeMb - 8)
```

## Visibility behavior

| Asset | Hide? |
|---|---|
| Sea / coast (`TILE_04_00_REST_BATCH_07`, `TILE_03_00`, `TILE_05_00`, water-like ids) | **never** |
| Near camera target | **never** |
| Screen-important | **never** |
| City layer | **never** (no holes, no coastline ring) |
| Heavy NEAR/MID | visible |
| Heavy FAR in frustum | visible |
| Heavy FAR out of frustum | hide only after hysteresis |
| Heavy CULL | hide after extra hysteresis |

INTERACTING still skips the visibility pass (STEP 21). No LOD work on the orbit path. No Box3 on the tick — manifest bounds cache only.

## Streamer integration

- Enqueue order = LOD score
- City tiles remain retained once loaded
- Heavy unload: old hysteresis **and** `dist > farM` **and** not sea **and** not look-at
- `resolveRuntimeAssetUrl` is identity — never `_lod2.glb` or `/lod1/`

## Integration with STEP 21 / 22

- INTERACTING: no new fetches, activation budget 0, no visibility pass
- SETTLING: 2 ms attach, no HEAVY/EXTREME attach
- IDLE: budgeted attach + LOD visibility at stream tick (500 ms)
- Parsed roots still wait READY off-scene; LOD only scores them

## Performance STEP 23 vs STEP 24

Safari / Intel live FPS was **not measured in this session** (unavailable). Do not treat the following as device FPS.

| | STEP 23 | STEP 24 |
|---|---|---|
| GLB files | 45 | **45** (unchanged; no LOD siblings) |
| City triangles | authored | **unchanged** (hide only) |
| Visibility | binary distance hide on all layers | city always on; heavy hysteresis |
| Extra draws | sky +1 MEDIUM/HIGH | **same** |
| Chunk | 708 kB | 714 kB |
| Priority / bounds CPU | — | instrumented in diagnostics (`priorityMs`, `boundsMs`); expected &lt; 1 ms for 45 rows |

Average FPS, interaction FPS, draw calls, and renderer memory on Safari: **unavailable** here. After a real load, Диагностика shows visible/hidden counts, active/hidden triangle estimates, and the two CPU timers.

## Tests

`npm test -- src/enterprise-city` → **139 passed**.

Covers: tiers, hysteresis, screen-space, frustum, target protect, sea protect, starvation, quality bands, bounds cache, priority order, activation order, 2D/3D remount, dispose, no invented LOD URLs, city layer never distance-hidden.

## Build

`npx vite build` → **PASS**.

## Limitations / future true LOD

- One mesh per asset; no geometric LOD
- Heavy hide is binary, not simplified proxy
- Screen-space uses bounding radius, not exact AABB
- Streamer still allocates a frustum matrix every 500 ms (pre-existing)
- Main-thread `GLTF.parse` remains the first-load hitch (STEP 22)

True LOD later: authored LOD0/1/2 URLs in the manifest, same scorer picking a level, never inventing paths. Worker parse is still a later step.

## Files changed

New: `src/web/src/enterprise-city/odessa3d/lod/*`, `docs/STEP_24_ODESSA_3D_LOD_VISIBILITY_RESULT.md`

Modified: `tileStreaming.ts`, `progressiveActivator.ts`, `odessaSceneController.ts`, `Odessa3DView.tsx`, `types.ts`, `index.ts`
