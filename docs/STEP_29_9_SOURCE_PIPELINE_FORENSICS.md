# STEP 29.9 — Odessa source pipeline forensics

Written **before** treating the rebuilt package as accepted. No calibration.
No STEP 30. This document answers Phase 1 only: where the last good source
is, which scripts produced the 45 GLBs, and the exact stage that collapsed
building footprints.

---

## ORIGINAL SOURCE

**`/Users/macbook/Downloads/Odessa.fbx`** (135 MB, 2022-07-09)

- Vendor: TurboCG OSM city (`extra_build_by_turbocg_com` survives in MASTER).
- Container: Kaydara FBX Binary.
- `UnitScaleFactor` = `1.0`, `OriginalUnitScaleFactor` = `1.0`.
  In the Autodesk FBX convention the default unit is **centimeters**, so
  the header declares **1 FBX unit = 1 cm**.
- `UpAxis` = 1 (Y), `FrontAxis` = 2 (Z), `CoordAxis` = 0 (X).
- Geometry itself is authored in **meters** (building heights named
  `height_95` / `height_199` are 95 / 199 raw units; merged `buildin100`
  vertical span is 23.67 raw units). Horizontal placement of those same
  meshes spans tens of kilometers of raw units — real Odessa scale, not
  a 600 m toy city.

The purchased/imported city is this FBX. There is no earlier source in
the repo or on the Desktop.

## LAST GOOD PRE-MERGE SOURCE

**`/Users/macbook/Desktop/Odessa_MASTER.glb`** (385 MB) plus
`Odessa_MASTER.blend` / `Odessa-3D_01_SOURSE_ODESSA_MASTER.BLEND/`.

MASTER is the converted city **before** the web tile export:

| | MASTER.glb | Runtime 45-GLB package |
|---|---|---|
| meshes | 1,834 | 1,835 |
| building node names | `buildin100`, `height_95`, `build`, … | `WEB_buildin100`, `WEB_height_95`, … |
| building node scale | **none (1.0)** | **uniform 0.01** |
| OSM / `base` node scale | 0.01 (21 objects) | 0.01 |
| `buildin100` POSITION min/max | `39393.9 × 50575.2 × 23.67` | **byte-identical** |
| `base` POSITION min/max | `61683.3 × 61683.3 × 0` | **byte-identical** |

`buildin100` raw buffers are identical in MASTER and `TILE_03_01.glb`.
The only material difference for buildings is the **node scale** the web
export wrote (1.0 → 0.01) and the `WEB_` rename / −90° X bake into the
Three.js Y-up frame.

Working copy used to produce tiles: `Odessa_WEB_WORK.blend`.
Intermediate export tree: `~/Desktop/ODESSA_WEB_EXPORT/` (same 45 GLBs
the runtime copies).

## CURRENT 45 GLB GENERATOR

Pipeline, backwards:

1. **Runtime ingest** — `scripts/build_odessa_runtime_package.py`
   (STEP 16). Copies `~/Desktop/ODESSA_WEB_EXPORT/**` →
   `src/web/public/assets/odessa/`, remaps Blender `bounds` (map-Y → Z,
   height-Z → Y), writes `odessa_manifest.json`. **Does not touch
   geometry or node scale.**
2. **Blender web export** — `Odessa_WEB_WORK.blend` →
   `ODESSA_WEB_EXPORT/`. Scripts living in the `.blend` (not in git)
   produced:
   - 14 top-level `TILE_XX_YY.glb`
   - `FINAL_TILE_04_REST/TILE_04_00_REST_BATCH_01..10.glb`
   - `HEAVY_BUILDING_CHUNKS/` (STEP 12 spatial split of the TILE_04 heavy mesh)
   - `HEAVY_BUILDING_CHUNKS_STEP13/` (STEP 13 sub-split of two oversized chunks)
   - `TILE_04_00.glb` (325 MB) is **intentionally excluded** from the
     runtime manifest (notes in the manifest).
3. **STEP 06 (in git)** — `~/Desktop/ODESSA_STEP_06.py`. Bounds + 8×8
   tile plan only. Header: `NO GEOMETRY WILL BE MODIFIED`.
4. **FBX → MASTER** — Blender import of `Odessa.fbx`. Honored the cm
   header for OSM/decal objects (those 21 nodes carry scale 0.01) but
   **left building meshes at scale 1.0** with meter vertices. This is
   why MASTER already contains mixed node-scale domains — it is *not*
   yet the footprint collapse.

## FIRST DESTRUCTIVE STAGE

**The Blender web-tile export (STEP 07–14), not the chunk merge.**

Every exported node in the 45 GLBs is a flat scene root with

```
scale ≈ [0.01, 0.01, 0.01]
```

and no `matrix`, no nested scaled parents (census:
`scripts/step29_9_node_census.mjs`, 1,833 nodes, 0 matrices, 0 unexpected
scales). Building meshes that were scale 1.0 / meter-authored in MASTER
were written out at 0.01. Vertex buffers were **not** resampled — they
are MASTER-identical.

Chunk merge (STEP 12/13) and `mergeBufferGeometries` are **not** the
unit bug. They only concatenate already-authored components. The
"miniature forest" STEP 29.8 measured is those MASTER-meter buildings
viewed through the export's 0.01 node scale.

## WHY FOOTPRINTS COLLAPSED

```
world_broken = T_export + R · (0.01 · v_master)
```

A 15.4 m MASTER building becomes 0.154 m. A 22 m nearest-neighbor
spacing becomes 0.22 m. STEP 29.8 compared 0.22 m spacing to a 15.4 m
*intended* footprint and concluded "placement destroyed". That comparison
assumed the 0.01 scale must stay (city stays ~600 m). Under that frame,
in-place ×100 of each component would overlap.

The correct frame: **placement and footprint were scaled together**.
NN 0.22 m × 100 = 22 m; footprint 0.154 m × 100 = 15.4 m. Buildings sit
next to each other with ~6 m gaps — a real city block. The layout was
never destroyed. It was uniformly interpreted as centimeters.

## WHY HEIGHTS / PLACEMENT DIVERGED (the mixed-domain illusion)

They did **not** diverge in the source. MASTER `height_95` raw Z-span is
exactly 95; `height_199` is exactly 199; `buildin100` vertical span is
23.67 m. After ×0.01 those become 0.95 / 1.99 / 0.24 m — the "100× too
flat" STEP 29.4–29.5 reported.

The *appearance* of two vertex domains inside one buffer was an
**observer-frame error**:

- Components ≥ 2 m after 0.01 looked like "already-correct metric
  buildings". They are the rare features whose MASTER size was already
  200 m+ (large blocks / merged slabs). STEP 29.8 repaired those 130 by
  stretching Y only — that was the wrong object.
- Components 0.15 m after 0.01 looked like "miniatures with destroyed
  placement". They are the normal 15 m MASTER buildings.

OSM / `base` already carried 0.01 in MASTER, so the export left them at
the same world size as the *crushed* buildings (~600 m). That is why the
broken package is internally consistent as a 600 m toy city, and why
removing 0.01 from **all** exported nodes restores buildings **and**
brings the decal/base stack up to the same ~60 km frame (MASTER `base`
world 616.8 m × 100 = 61.7 km, covering the restored city).

## PHASE 2 DECISION — DO NOT RE-MESH FROM THE 45 GLBs

The 45 GLBs are **output**. Their **vertex buffers are the last good
source** (MASTER-identical). The rebuild is therefore a unit-
interpretation rewrite of the glTF JSON (translation ×100, scale 0.01 →
1.0), not a reconstruction of triangles from the broken world-space
view, and not a second Blender export (STEP 07–14 scripts are not in
git; re-running them is how the bug was introduced).

`Odessa.fbx` is the original, but Three.js `FBXLoader` plus a from-
scratch tile split would recreate STEP 06–14 without the working
Blender scripts. MASTER.glb is the last good pre-merge scene; using its
already-tiled, already-axis-converted buffers via the 45-GLB JSON fix
preserves streaming filenames and the manifest.

## REBUILD RULE (implemented)

```
world_metric = 100 · T_export + R · v_master = 100 · world_broken
```

1 world unit = 1 meter. No mixed cm/m node scales. Geometry BIN chunks
are copied byte-for-byte. See `scripts/step29_9_build_metric_package.mjs`.

STOP. STEP 30 not started. Calibration not performed.
