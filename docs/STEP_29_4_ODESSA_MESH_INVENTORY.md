# STEP 29.4 — Odessa GLB Mesh Inventory (Phase 2/5)

Date: 2026-08-23
Generator: `src/web/scripts/step29_4_glb_inventory.mjs` (offline; parses the glTF JSON chunk of
every GLB — accessor min/max gives exact local AABBs, node TRS hierarchies are composed to world
space; no geometry decode, no runtime needed).
Full machine-readable output: `src/web/scripts/step29_4_inventory.json`
(per-mesh: name, parent path, mesh/material indices, material name, alphaMode, doubleSided,
baseColor, metallic/roughness, vertex/triangle counts, local + world AABB, TRS, flags).

## Totals

| Metric | Value |
| --- | --- |
| GLB files | 45 (all referenced by `odessa_manifest.json`) |
| Mesh primitives | 1,835 |
| Triangles | 8,025,248 |
| Computed city bounds (world) | X [−417.8, 317.6] · Y [−0.2, **2.0**] · Z [−658.1, 389.5] |
| Manifest cityBounds Y | [−0.165, 1.990] — **matches computed: the whole city is under 2 m tall** |
| Suspicious flagged meshes | 319 |
| Exact duplicate groups | 21 |
| Coplanar overlapping flat pairs | 33,322 |

## Critical finding 1 — the city is 100× flatter than intended

The tallest mesh in the entire 383 MB package is **1.99 m**. Mesh names encode the intended
height, and every one renders at exactly 1/100 of it:

| Mesh | Intended height (from name) | Actual world height |
| --- | --- | --- |
| `WEB_height_199` (TILE_04_04) | 199 m | 1.990 m |
| `WEB_height_95` (TILE_05_02) | 95 m | 0.950 m |
| `WEB_height_80` (TILE_04_02) | 80 m | 0.800 m |
| `WEB_height_75` (TILE_03_02) | 75 m | 0.750 m |
| `WEB_height_60` (TILE_04_01) | 60 m | 0.600 m |

The XZ footprint is correct (~735 × 1048 m — real Odessa districts), so the export wrote
vertical extents 100× too small (heights authored in meters while the horizontal plane was in
centimeters; the global node scale 0.00999… converts XZ correctly and squashes Y).
Raw accessor data confirms this (e.g. `HEAVY_BUILDING_CHUNK_00_00` raw span 9.79 units ≈ 0.098 m
world). **This is intrinsic to the source GLB vertex data — not a runtime, loader, or transform
bug.** Zero meshes exceed 2 m; zero meshes extend below −0.2 m; nothing pierces sea level from
below.

## Critical finding 2 — the mm-spaced coplanar decal stack

The model is a layered OSM-style 2.5D map. Flat city-wide polygon layers are stacked
**1–5 millimeters apart** around y = 0:

| Authored Y (m) | Layers | Content |
| --- | --- | --- |
| −0.005 | 1 | `WEB_base` (base quad) |
| −0.003 | 13+ | `WEB_name_*` label polygons, some landuse |
| −0.002 | 42 | `WEB_landuse_*`, `WEB_amenity_*` |
| 0.000 | 5 | `WEB_water`, `WEB_rivers` |
| +0.001 | 12 | `WEB_natural_*` |
| +0.003 | 108 | `WEB_leisure_*`, more landuse |
| 0 → +0.005 | 43 | `WEB_highway_*`, `WEB_route_*` road ribbons (h ≈ 0.01) |

33,322 pairs of these flat meshes overlap in XZ within 0.5 mm of each other's plane.

Depth-precision consequence (24-bit depth, near = 2.56): resolvable depth at distance z is
≈ z²/(near·2²⁴) → 0.2 mm @100 m, **2.1 mm @300 m, 8.4 mm @600 m, 23 mm @1000 m**. Beyond
~300 m the buffer cannot separate layers authored 1–5 mm apart → massive z-fighting, worst at
grazing (oblique/low) angles where depth slope per pixel is maximal. Top-down close views stay
under the threshold — exactly the observed behavior.

## SUSPICIOUS LARGE MESHES

Exact object names, flagged `CITY_WIDE_FOOTPRINT` and/or `FLAT_SLAB` (full list of 319 in the
JSON):

| Object | File | Material | Footprint (m) | Height (m) | Y | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **`WEB_base`** | `FINAL_TILE_04_REST/TILE_04_00_REST_BATCH_10.glb` | `map` (no texture, baseColor 0.59/0.60/0.52 = **matte gray**), doubleSided | 616.8 × 616.8 | 0.000 | −0.005 | **2 triangles — the gray slab** |
| `WEB_water` | `…REST_BATCH_07.glb` | `Water`, doubleSided | 627.5 × 952.1 | 0.000 | 0.000 | sea/harbor polygon |
| `WEB_natural_wo` | `…REST_BATCH_07.glb` | `natural.001`, doubleSided | 652.6 × 676.8 | 0.000 | +0.001 | |
| `WEB_landuse_f0` | `…REST_BATCH_06.glb` | `natural` / `landuse.002`, doubleSided | ~636 × 665 | 0.000 | −0.002 | |
| `WEB_route_road_1` | `…REST_BATCH_03.glb` | (default) | 708.6 × 959.5 | 0.010 | 0→0.005 | 42,638-tri road web |
| `WEB_highway_unclassified_1` | `…REST_BATCH_05.glb` | (default) | 635.5 × 658.0 | 0.010 | 0→0.005 | |
| `WEB_barrier_w1` | `…REST_BATCH_02.glb` | (default) | 556.1 × 588.9 | 0.010 | 0→0.005 | 99,384 tris |
| `WEB_rivers` | `TILE_03_00.glb` | `Water`, doubleSided | 614.5 × 611.1 | 0.020 | ±0.01 | |
| `WEB_build` | `…REST_BATCH_01.glb` | `building`, doubleSided | 416.6 × 544.2 | 0.390 | −0.165→0.222 | 370,936-tri merged building mass — flattened 100× |

## EXACT DUPLICATES

21 groups, **all** `WEB_name_____N` OSM label polygons inside
`FINAL_TILE_04_REST/TILE_04_00_REST_BATCH_10.glb` — identical triangle counts and identical
world AABBs, duplicated up to **83×** (`WEB_name_____0` … `WEB_name_____0_83`), all coplanar at
y = −0.003. These are overlapping rendered instances (not shared-geometry reuse) and pure
z-fighting fuel with zero visual value. Full list in the JSON (`duplicateGroups`).

## PROBABLE COPLANAR DUPLICATES / OVERLAPPING LARGE PLANES

33,322 flat-mesh pairs overlap >50 % in XZ within 0.5 mm in Y. Dominated by the
landuse/natural/leisure/name stack listed above. This is the striped-artifact engine.

## Scene attachment audit (Phase 5)

- Odessa root instances in scene: **1** (`odessaCityRoot`, parent-guarded since STEP 29.2;
  `renderStability.cityRootInstances` diagnostic confirms at runtime).
- Runtime adds **no** sea plane, **no** terrain plane, **no** full-screen quads — the only
  generated geometry is small geo/calibration markers, Box3 helpers, and a dev-flag-gated
  placeholder box (`VITE_ODESSA_DEBUG_PLACEHOLDER`, off by default). The slab and stripes are
  100 % source-GLB content.
- Geometry/material reuse via `MaterialInternCache` is reference sharing, not duplicate
  instances (verified: intern merges only identical untextured materials; STEP 29.4 adds
  polygonOffset to the intern key so decal ranks can never merge).
