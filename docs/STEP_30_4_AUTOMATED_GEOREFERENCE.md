# STEP 30.4 — Automated Odessa georeference

Date: 2026-08-23

STEP 31 was **not** started. No A/B/C GPS was invented. Scale was
**not** forced to 1. Geometry, GLB, `odessa_metric`, STEP 29 repairs,
camera, and OrbitControls were **not** modified.

---

## Status

`GEOREFERENCE_STATUS = BLOCKED`  
`SAFE_TO_START_STEP_31 = NO`

A production pipeline now exists (parser → exact-name mapper →
production similarity solver + RANSAC → schema v4 persist). It did
**not** persist a live transform, because no proven model↔WGS84
correspondences exist.

---

## Public landmarks

Local repo has no OSM dump / GeoJSON of Odessa POIs
(`ukraine-oblasts.geojson` is oblast polygons only).

Cited public catalog (parser cache, **not** used as controls):

| id | name | GPS | source |
| --- | --- | --- | --- |
| wikidata-Q195513 | Odesa Opera and Ballet Theatre | 46.485556, 30.741667 | Wikipedia / Wikidata Q195513 |

Overpass/OSM node fetch timed out. OSM node `4531723653` was opened
by the operator in Safari; its coordinates were **not** copied into
the catalog (unverified from this environment).

`PUBLIC_LANDMARKS_FOUND = 1`

---

## Model landmarks

`step29_6_inventory.json`: 1835 meshes. Names are OSM **class** tags
(`WEB_build`, `WEB_highway_*`) or Cyrillic `WEB_name_*` labels
stripped to underscores.

Readable unique tokens that are **not** generic classes:

- `WEB_name_____FONTAN_SKY_1`
- `WEB_name_________Kyivstar_1`
- `WEB_name_Sheriff_Pilott_1`
- class meshes such as `WEB_man_made_lighthouse_1` (not a named
  Vorontsov lock)

None of these normalize to “odesa opera” / opera aliases.

`MODEL_LANDMARKS_MATCHED` (token-bearing names) = 228  
`SEMANTIC_MAPPING_FOUND` = 0

Matching `WEB_man_made_lighthouse_1` or `WEB_highway_steps_1` to a
famous place would be a guess. Forbidden.

---

## Solver / CHECK / scale

No A/B/C were synthesized. The production solver was **not** applied
to invented points.

Historical CHECK (operator STEP 30.1, independent, never in solver):

- world = −1935.01, 20.66, 15514.82
- actual GPS = 46.386267, 30.705832
- predicted GPS (reported) = 46.386292, 30.705357
- error ≈ 36.58 m (ΔE ≈ −36.47, ΔN ≈ +2.78)

That discrepancy **cannot** be shown to disappear without a new
transform.

Pair scales / solver scale: not computed on real controls. The old
UI scale 1.4475 remains unexplained. Package still claims 1 wu = 1 m.

---

## Persistence / camera / geometry

Schema v4 save/reload is implemented and tested on **synthetic**
exact-name fixtures only. Live storage was not written.

Vertex hashes, X/Z geometry, STEP 29 repair, hover/select,
OrbitControls, and 2D/3D were not touched.

---

## Tests / build

Enterprise-city: 355 passed / 1 skipped.  
Geospatial includes parser, ENU, similarity, axis, RANSAC, LOO,
CHECK exclusion, v4 reload, historical CHECK, scale pairs,
geometry-import invariance.  
`npx vite build`: PASS.
