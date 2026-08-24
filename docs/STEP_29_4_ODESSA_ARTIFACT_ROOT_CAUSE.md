# STEP 29.4 — Odessa 3D Artifact Root Cause

Date: 2026-08-23
Scope: `src/web/src/enterprise-city/odessa3d/`
No calibration performed. STEP 30 not started.
Companion evidence: `docs/STEP_29_4_ODESSA_MESH_INVENTORY.md` +
`src/web/scripts/step29_4_inventory.json` (full per-mesh inventory of all 45 GLBs).

---

## Root cause (proven from source data, not guessed)

The artifacts come from the **source GLB itself**, established by an offline inventory of every
mesh in all 45 GLB files (exact AABBs from glTF accessor min/max + composed node transforms):

1. **The gray slab is `WEB_base`** — a 616.8 × 616.8 m, **2-triangle**, untextured, double-sided
   quad in `FINAL_TILE_04_REST/TILE_04_00_REST_BATCH_10.glb`, material `map` with matte
   gray-green baseColorFactor (0.594, 0.600, 0.522), at y = −0.005. At low camera angles it
   (plus the untextured landuse layers above it) fills the view nearly edge-on.
2. **The dark/striped regions are z-fighting inside a millimeter-spaced coplanar decal stack.**
   The model is a layered OSM map: 166 flat city-wide layers authored 1–5 mm apart
   (base −0.005 → labels −0.003 → landuse −0.002 → water 0.000 → natural +0.001 →
   leisure +0.003 → roads 0→+0.005), 33,322 overlapping coplanar pairs. With a 24-bit depth
   buffer and near = 2.56, resolvable depth at distance z is ≈ z²/(near·2²⁴):
   2.1 mm @300 m, 8.4 mm @600 m, 23 mm @1000 m — beyond ~300 m the buffer cannot separate the
   authored gaps. Grazing (oblique/low) angles maximize per-pixel depth slope, top-down close
   views stay under the threshold — exactly matching the observed angle dependence.
3. **The whole city is 100× flatter than intended** (source-export defect, reported, NOT
   "fixed" at runtime): `WEB_height_199` (a 199 m building) is 1.99 m tall; `WEB_height_95` →
   0.95 m; `WEB_height_80` → 0.80 m; etc. Tallest mesh in the entire package: 1.99 m over a
   735 × 1048 m footprint. Heights were exported in meters while the horizontal plane was in
   centimeters; the global 0.01 node scale flattens Y 100×. This is why the "city" reads as a
   flat slab at low angles at all — there is almost no vertical geometry to occlude the ground
   stack. Correcting it requires a re-export (or an explicit product decision on a Y-scale
   correction); it is out of STEP 29.4 scope and was not touched.
4. **Real duplicates exist**: 21 groups of `WEB_name_____N` OSM label polygons in
   `…REST_BATCH_10.glb`, identical world AABBs duplicated up to 83×, all coplanar at −0.003 —
   additional z-fight contributors inside the same stack.

Runtime layers were ruled out by code audit: the runtime generates **no** sea plane, **no**
terrain plane and no full-screen geometry (only small markers/helpers and a dev-flag-gated
placeholder box, off by default). `odessaCityRoot` is attached exactly once.

## Fix applied (Phase 10 — smallest safe, category "coplanar / depth settings")

**Deterministic polygon-offset layering of the ground-decal stack**
(`renderDebugTools.ts::applyGroundDecalLayering`, invoked from `scenePrep.prepareParsedScene`):

- A mesh is a *ground decal* iff its world AABB is ≤ 20 mm thick **and** lies within ±60 mm of
  y = 0 (the authored band). Buildings (0.08–1.99 m) and elevated flats are excluded.
- Each decal gets `polygonOffset` with factor/units proportional to its authored Y rank
  (1 mm resolution), preserving the exporter's stacking order exactly — layers above are biased
  toward the camera by whole depth-resolution units, so the GPU separates them at **every**
  distance and angle.
- Shared materials used by non-decal meshes (e.g. the GLTF default material shared by road
  ribbons and flat buildings) are **cloned per rank** — building geometry is never depth-biased.
- `materialInternKey` now includes polygonOffset so the intern cache can never merge two ranks.
- polygonOffset changes only depth-buffer values: **no vertex, color, texture, transform,
  georeference, picking, or fingerprint change.** Idempotent (userData-guarded), applied once
  per parsed asset, never in the render loop.

Why not near/far tuning alone (Phase 6 answer): even a perfect near of 10 m yields ~2 mm
resolution at 600 m — still ≥ the 1–5 mm authored gaps. Depth precision is *involved* but
mathematically cannot resolve this stack by itself; logarithmic depth was already evaluated and
kept off in 29.2 (Safari cost, disables early-Z); **reverse-Z is not supported** by the three.js
0.170 WebGL backend (WebGPU-only feature) — reported unsupported, not enabled.

## Diagnostics added (dev-only, Phase 1/3/4/9)

All under the DEV panel (`showDev`), none persisted, none active by default:

- **SOURCE CITY ONLY** — hides every scene child except the imported GLB hierarchy (environment,
  fog, background, markers, helpers, overlays all off; neutral ambient light so the GLB is
  visible). Plus: ENV OFF, NEUTRAL LIGHT, WIREFRAME, DEPTH DEBUG (MeshDepthMaterial override),
  SIDE: ORIGINAL/FRONT/DOUBLE cycle, TRANSPARENT OFF, MESH BOUNDS (per-asset Box3 helpers),
  HIDE BASE PLANE (exact-name `WEB_base` only), TIGHT CLIP (depth A/B comparison on the same
  pose). Material mutations are snapshot/restored — dev toggles never leak into materials.
- **ALT/OPTION + CLICK inspector** — raycasts the rendered geometry and prints
  OBJECT / PARENT / MATERIAL / GEOMETRY / WORLD POSITION / FACE / BOUNDING BOX / distance /
  box height / decal rank to the console and the "Artifact isolation (29.4)" panel. Clicking the
  gray slab identifies `WEB_base` directly.
- **Binary mesh bisection** — BISECT ON / ALL / HALF A / HALF B / NEXT SPLIT / RESET /
  BISECT OFF over a deterministically sorted mesh list; at ≤8 remaining meshes their exact
  names are listed. Visibility snapshot restored on BISECT OFF.
- **Camera-altitude report** in diagnostics: camera Y, city base Y, altitude above base,
  inside-bounding-box / below-base / below-sea flags — live during orbit (Phase 9). Note: with a
  2 m-tall city, near-horizontal orbits put the camera close to base height by design; the slab
  is legitimate source geometry seen edge-on, not camera-below-ground traversal.

## Phase answers

| Question | Answer |
| --- | --- |
| SOURCE CITY ONLY CLEAN | **NO** — the artifact is inside the source GLB (decal stack + flat heights); isolation mode proves it persists with all runtime layers off |
| GRAY SLAB OBJECT | `WEB_base` (2-triangle 616.8×616.8 m quad, material `map`, y=−0.005) + untextured landuse stack above it |
| GRAY SLAB SOURCE | **GLB** (not water, not terrain, not overlay) |
| STRIPED ARTIFACT ROOT CAUSE | z-fighting between 166 coplanar OSM decal layers authored 1–5 mm apart (33,322 overlapping pairs) — depth resolution at >300 m exceeds the gaps |
| RESPONSIBLE OBJECT(S) | `WEB_base`, `WEB_landuse_*`, `WEB_natural_*`, `WEB_leisure_*`, `WEB_amenity_*`, `WEB_name_____N` (dup ×83), `WEB_highway_*`/`WEB_route_*`, `WEB_water`/`WEB_rivers` |
| RESPONSIBLE MATERIAL(S) | `map`, `landuse(.002/.003)`, `natural(.001)`, `leisure`, `area`, `name(.001)`, `Water`, GLTF default material |
| DUPLICATE GEOMETRY FOUND | **YES** — 21 groups of `WEB_name_____N` label polygons (identical world AABBs, up to 83 instances) |
| COPLANAR GEOMETRY FOUND | **YES** — 33,322 overlapping flat pairs within 0.5 mm |
| CAMERA BELOW BASE FOUND | **NO** as root cause — logging added; slab visibility is edge-on legitimate geometry, not sub-ground traversal |
| DEPTH PRECISION INVOLVED | **YES** — precision at distance exceeds the mm gaps; but near/far tuning alone cannot fix it (see math above) |
| WATER INVOLVED | **NO** — `WEB_water` is one member of the stack like any other; water code mutates nothing globally |
| OVERLAYS INVOLVED | **NO** — runtime adds no large geometry; all flagged meshes are GLB content |
| FIX APPLIED | Deterministic polygonOffset decal layering (depth-bias only) + intern-key rank safety; regression tests added |
| SOURCE GLB VERTICES MODIFIED | **NO** |
| GEOREFERENCE MODIFIED | **NO** |
| CALIBRATION MODIFIED | **NO** |

## Files changed

| File | Change |
| --- | --- |
| `renderDebugTools.ts` (new) | decal classifier/rank/layering fix; material debug override; MeshBisector; inspector; camera-altitude report; base-plane toggle |
| `scenePrep.ts` | invokes `applyGroundDecalLayering` once per parsed asset; result in `PreparedSceneInfo` |
| `materialIntern.ts` | polygonOffset added to intern key (ranks never merge) |
| `odessaSceneController.ts` | debug-view state/apply, bisect API, ALT+click inspector, `artifactDebug` diagnostics, dispose cleanup |
| `types.ts` | `artifactDebug` diagnostics typing |
| `Odessa3DView.tsx` | 29.4 debug buttons + "Artifact isolation (29.4)" panel |
| `scripts/step29_4_glb_inventory.mjs` (new) | offline GLB inventory generator |
| `renderDebugTools.test.ts` (new) | 8 regression tests for the root cause and tooling |

## Validation

- TESTS: **259 passed / 0 failed** (`npx vitest run src/enterprise-city`; 251 baseline + 8 new
  root-cause regression tests). Full-workspace suite unchanged: same 12 pre-existing failures in
  unrelated modules, none in enterprise-city.
- BUILD: **PASS** (`npx vite build`, 16.9 s).
- MANUAL SAFARI VALIDATION REQUIRED: **YES** — orbit the 8 poses (top-down, 45°, low oblique,
  near-horizontal, central close, port, coastline, 360°). Expected: stripes gone (decal ranking),
  slab identifiable via ALT+click, and — because the source city is 100× flat — the horizon view
  will still look like a thin map until the GLB heights are re-exported (that is source data,
  not render instability).

```
SOURCE CITY ONLY CLEAN: NO (artifact is in the source GLB — proven)
GRAY SLAB OBJECT: WEB_base (FINAL_TILE_04_REST/TILE_04_00_REST_BATCH_10.glb)
GRAY SLAB SOURCE: GLB
STRIPED ARTIFACT ROOT CAUSE: mm-spaced coplanar OSM decal stack z-fighting
RESPONSIBLE OBJECT(S): WEB_base, WEB_landuse_*, WEB_natural_*, WEB_leisure_*, WEB_name_____N, WEB_highway_*, WEB_water
RESPONSIBLE MATERIAL(S): map, landuse.*, natural.*, leisure, area, name.*, Water, GLTF default
DUPLICATE GEOMETRY FOUND: YES (WEB_name label polygons, up to 83×)
COPLANAR GEOMETRY FOUND: YES (33,322 pairs)
CAMERA BELOW BASE FOUND: NO
DEPTH PRECISION INVOLVED: YES (contributing, not fixable by near/far alone)
WATER INVOLVED: NO
OVERLAYS INVOLVED: NO
FIX APPLIED: deterministic polygonOffset decal layering (depth-only bias)
SOURCE GLB VERTICES MODIFIED: NO
GEOREFERENCE MODIFIED: NO
CALIBRATION MODIFIED: NO
TESTS: 259 passed / 0 failed
BUILD: PASS
MANUAL SAFARI VALIDATION REQUIRED: YES
SAFE TO CALIBRATE: NO — until manual Safari orbit is visually clean
```

**STOPPED after STEP 29.4. No calibration. No STEP 30.**
