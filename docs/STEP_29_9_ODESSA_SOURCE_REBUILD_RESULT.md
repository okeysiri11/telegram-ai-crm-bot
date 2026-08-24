# STEP 29.9 — Odessa source rebuild result

Follows `docs/STEP_29_9_SOURCE_PIPELINE_FORENSICS.md`. No calibration.
STEP 30 not started.

---

## SOURCE USED

Last good pre-merge scene: **`Odessa_MASTER.glb`** (Desktop), whose
building vertex buffers are **byte-identical** to the 45 runtime GLBs.

Original purchased model: **`Odessa.fbx`** (TurboCG 2022, header
`UnitScaleFactor=1` = centimeters, geometry authored in meters).

Rebuild input: the existing 45-GLB export JSON + BIN (BIN = MASTER
geometry). Not remeshed. Not re-exported from Blender (those scripts
introduced the 0.01 scale).

Output: `src/web/public/assets/odessa_metric/` (45 GLBs + manifest).
Builder: `src/web/scripts/step29_9_build_metric_package.mjs`.

## DESTRUCTIVE PIPELINE BUG FOUND

**YES**

## BUG LOCATION

Blender web-tile export (STEP 07–14 in `Odessa_WEB_WORK.blend`), not
chunk merge, not `mergeBufferGeometries`, not the runtime loader.

Every exported node was written with uniform `scale ≈ 0.01` because the
FBX header declared centimeters. Building meshes in MASTER were already
meter-authored at scale 1.0. The export multiplied them by 0.01 without
baking a unit conversion into the buffers. OSM/`base` already carried
0.01 in MASTER, so the crushed buildings lined up with a ~600 m toy
city — internally consistent, globally 100× too small.

Exact identity:

```
world_broken = T + R · (0.01 · v)
world_metric = 100·T + R · v     (scale → 1, translation ×100)
```

All 1,833 nodes are flat roots, no matrices (node census). BIN chunks
copied byte-for-byte.

## OLD PACKAGE BUILDINGS

Broken package (`/assets/odessa`), after STEP 29.8 runtime repair:

- ~197,710 components classified "miniature" (0.15 m foot, 0.17 m tall,
  0.22 m spacing) — actually 15 m MASTER buildings seen through 0.01
- 130 components "repaired" by Y×100 only (wrong object)
- 128,642 needle components if whole-mesh Y×100 is applied
- `WEB_height_95` / `WEB_height_199` rendered at 0.95 m / 1.99 m
- city AABB ~735 × 2 × 1048 m

## NEW PACKAGE BUILDINGS

Phase 10 audit (`scripts/step29_9_validate_metric.mjs`) over all 45
metric GLBs, welded components, final world space:

```
GLB count:                              45
mesh count:                             1,835
welded components (building meshes):    699,074
building-like components (h > 0.02 m):  272,222

footprint  min=1.30  median=17.34  P95=62.79  max=1169.10 m
height     min=0.10  median=14.61  P95=21.56  max=199.00 m
```

`WEB_height_95` / `WEB_height_199` raw Z-span is 95 / 199 and now
renders at those meters (scale 1). `WEB_base` is a 61.7 km ground
quad covering the restored city (MASTER `base` 616.8 m × 100).

11 extreme-aspect components and 2 vendor-authored slender towers
(`WEB_building_8` 19.1×1.4 m, `WEB_building81` 17.0×2.1 m) are
flagged, not destroyed (Phase 4). Sampled degenerate triangles (4,830)
are vendor FBX geometry, unchanged.

## MINIATURE COMPONENTS BEFORE

197,710 (STEP 29.8, broken package, 0.01 frame)

## MINIATURE COMPONENTS AFTER

**0**

## NEEDLES BEFORE

128,642 (whole-mesh Y×100 on mixed buffers) / visual needle forest in
Safari on the 0.01 package

## NEEDLES AFTER

**0**

## CITY MAX HEIGHT

**199.00 m** (`WEB_height_199`)

## MEDIAN BUILDING HEIGHT

**14.61 m**

## MEDIAN BUILDING FOOTPRINT

**17.34 m**

## 45 GLBs REBUILT

**YES** — deterministic filenames, same tile / batch / STEP-12 / STEP-13
layout, `packageFormat: blender_web_v1_metric`.

## OLD PACKAGE PRESERVED

**YES** — `src/web/public/assets/odessa/` untouched. DEV panel
`PKG: METRIC | BROKEN` swaps via `localStorage` + reload
(`odessaPackage.ts`).

## RUNTIME ×100 HACK REQUIRED

**NO** on the production path.

`scenePrep` reads `activeOdessaPackage().runtimeGeometryRecovery`.
`REBUILT_METRIC` (default) sets it **false**: no `verticalRecovery`, no
`componentRepair`, no needle rollback. Those modules remain in-tree
behind the `CURRENT_BROKEN` rollback flag and DEV toggles only.

Decal ranking (STEP 29.4) is kept; `decalYScale=100` so the same
polygonOffset order applies to the 0.1 m metric stack. Camera near cap
scales with the ~84 km diagonal (`cameraNearMaxFor`) and still tightens
at street distance. Water-duplicate Y thresholds scale the same way.

Phase 7 (re-batch / split giant meshes) and Phase 13 (Draco / meshopt)
were **not** done — correctness first.

## SAFARI VISUAL VALIDATION

**NOT RUN IN THIS SESSION**

Hard-refresh Safari against `REBUILT_METRIC` (default) is still
required before STEP 30. Checklist: overview, low horizon, 45°,
top-down, center, port, coast, dense residential, outer districts,
building-level zoom. Numerical audit is PASS; visual sign-off is not
claimed.

## TESTS

**PASS** — enterprise-city suite 303 passed / 1 skipped (package A/B,
metric clip, metric decal rank, existing 29.4–29.8). Phase 10 offline
audit PASS (needles=0, miniatures=0, invalid transforms=0, NaN=0).

## BUILD

**PASS** (`vite build`, 38.9 s).

## SAFE TO CALIBRATE

**NO** until Safari visual PASS. Geometry is metric and X/Z of the
source buffers are unchanged relative to MASTER; georeference code is
untouched. Do not start STEP 30.

## ARCHITECTURAL DECISIONS

1. **Unit-interpretation rebuild over Blender re-export.** STEP 07–14
   scripts are not in git; they are the bug. MASTER buffers already
   live in the 45 GLBs.
2. **Do not XYZ-scale individual components.** Placement and footprint
   share the same 0.01; a uniform node fix restores both.
3. **Keep the 45-file streaming layout.** Phase 7 hierarchical rebatch
   deferred until visual PASS (Phase 13).
4. **A/B, do not delete.** `CURRENT_BROKEN` remains the rollback.
5. **Production path renders the metric source directly.** Recovery
   hacks are legacy-only.

STOP AFTER STEP 29.9.
