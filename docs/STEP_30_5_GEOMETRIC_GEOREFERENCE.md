# STEP 30.5 — Geometric Odessa georeference

Date: 2026-08-23

STEP 31 was **not** started. No A/B/C GPS was invented. Scale was
**not** forced to 1. Geometry, GLB, `odessa_metric`, STEP 29 repairs,
camera, and OrbitControls were **not** modified.

`GEOMETRY_CHANGED = NO`  
`STEP29_REPAIR_CHANGED = NO`

---

## Status

`GEOREFERENCE_STATUS = BLOCKED`  
`SAFE_TO_START_STEP_31 = NO`

A production geometry pipeline now exists (OSM parser → model X/Z
signatures → unique footprint + constellation matching → production
similarity solver + RANSAC → independent CHECK quality → schema v4
persist). It did **not** persist a live transform.

Independent CHECK quality (this step):

| Grade | CHECK_RMS | CHECK_P95 |
| --- | --- | --- |
| EXCELLENT | ≤ 5 m | ≤ 10 m |
| GOOD | ≤ 10 m | ≤ 20 m |
| ACCEPTABLE | ≤ 20 m | ≤ 35 m |
| FAILED | worse | worse |

PASS requires independent validation. Control fit is diagnostic only.
No independent CHECK set exists for a new transform, so the live run
cannot be graded EXCELLENT/GOOD/ACCEPTABLE.

---

## OSM source

Fetched from Overpass (`overpass-api.de`), cached under
`src/web/src/enterprise-city/odessa3d/geospatial/osm_cache/`.

| Layer | Query / bbox | Count |
| --- | --- | --- |
| Buildings | `way[building]` downtown (46.475,30.725)–(46.495,30.755), `out bb` | 2568 |
| Roads | `highway` primary/secondary/trunk/tertiary (46.45,30.68)–(46.52,30.80) | 867 |
| Coastline | `natural=coastline` | 51 ways / 2534 vertices |
| Distinctive buildings | theatre/hospital/university/worship + attractions, `out geom` | 106 |

`OSM_SOURCE = overpass-api.de`  
`OSM_BUILDING_COUNT = 2568`  
`OSM_ROAD_COUNT = 867`

---

## Model X/Z signatures

Read-only AABB extract from `odessa_metric` GLB accessors
(`src/web/scripts/step30_5_model_signatures.json`). 1835 meshes.

| Class | Total | Local (usable for matching) | City-wide batches |
| --- | --- | --- | --- |
| Building | 153 | 23 (8–250 m) | 118 |
| Road | 62 | 4 | 57 |
| Water | 6 | 1 well (15 m) | 5 (up to ~63 × 95 km) |
| Coast-like `WEB_natural_*` | 3 | 1 sand AABB 1.7 × 0.7 km | 2 city-scale |

`MODEL_BUILDING_CANDIDATES = 23`  
`MODEL_ROAD_CANDIDATES = 4`

Source geometry precision is **lower than OSM footprints**. Most
“buildings” are merged class layers, not individual houses. That is
reported, not scored away.

---

## Matching (no names, no guesses)

Rules:

1. Compare unordered footprint `{min,max}` spans within 15%.
2. Require **bidirectional uniqueness** (one model ↔ one OSM).
3. Require a **constellation of ≥ 3** whose pair-scales agree (spread ≤ 15%).
4. Require spatial distribution (not collinear, ≥ 200 m separation, ≥ 2 regions).
5. Reject size-unique pairs that fail (3)–(4). Size-unique in a cropped bbox is not identity.

Live result:

- `RAW_MATCHES = 2522` size candidates
- Bidirectional unique downtown leftovers: 2
  (`WEB_building42` ↔ OSM 42344743, `WEB_building37` ↔ OSM 160351765)
- Those two are anonymous OSM footprints vs generic `WEB_building*` meshes
- World distance ≈ 9878 wu, GPS distance ≈ 1270 m → implied pair scale ≈ 7.8
- That is neither 1.0 nor 1.4475, so the pair is **not** a consistent lock
- `RANSAC_INLIERS = 0` (solver never ran on live correspondences)
- `MATCHED_REGION_COUNT = 0`
- Accepted identity matches = 0

Roads: local model roads are railway/pipeline AABBs, not street
centerlines. No unique road constellation.

Coastline: OSM shoreline exists. The model has water/sand **boxes**,
not a coastline polyline.

`COASTLINE_MATCH_AVAILABLE = NO`  
`COASTLINE_RMS_M = n/a`  
Precision note: `MODEL_COAST_IS_AABB_NOT_A_POLYLINE`

---

## Scale 1.4475 investigation

Historical STEP 30.1 solver reported `WORLD_UNITS_PER_METER = 1.4475`
from unpublished A/B/C. Package claim is 1 wu = 1 m.

Independent pair-scale distribution on **accepted** live matches:

```
PAIR_SCALE_COUNT=0
PAIR_SCALE_MEDIAN=n/a
PAIR_SCALE_MEAN=n/a
PAIR_SCALE_STDDEV=n/a
PAIR_SCALE_P05=n/a
PAIR_SCALE_P95=n/a
```

`SCALE_1_4475_SUPPORTED = NO` — no accepted pair set whose median sits
near 1.4475 (±8%) with low spread.

`SCALE_1_0_SUPPORTED = NO` — same, for 1.0.

Evidence against treating the two rejected size-unique buildings as
support for either hypothesis: their implied scale is ~7.8.

Synthetic fixtures in tests recover 1.0 and 1.4475 when the
correspondences are known. That does not license a live scale.

---

## Historical CHECK (never in the solver)

No new transform was applied, so the reported STEP 30.1 CHECK stands:

- world = −1935.01, 20.66, 15514.82
- actual GPS = 46.386267, 30.705832
- predicted GPS (reported) = 46.386292, 30.705357
- error ≈ 36.58 m (ΔE ≈ −36.47, ΔN ≈ +2.78)

`INDEPENDENT_CHECK_COUNT = 0` for a new geometric solve.

---

## Persistence / geometry

Schema v4 persist runs only if independent CHECK is ACCEPTABLE or
better. Live run did not persist.

Geographic transform is metadata only. Render transform was not
applied. `odessaCityRoot` remains identity.

---

## Architectural decisions

1. **Extend** the existing similarity solver / RANSAC / v4 store. Do
   not add a second georeference engine.
2. **Reject** size-only matches without a consistent 3+ constellation.
   Unique AABB in a downtown crop is not a landmark.
3. **Do not** score coastline RMS against city-wide water AABBs.
   That would fabricate a better grade than the source supports.
4. Operator A/B/C remain the remaining path **after** these geometry
   methods were exhausted. They were not requested in this step.

---

## Tests / build

Enterprise-city vitest: **369 passed / 1 skipped**  
`npx vite build`: **PASS**

Covered: OSM parser, model X/Z signatures, axis mapping search,
similarity, RANSAC, coastline metric, building matching, road
matching, spatial distribution, held-out validation, pair-scale
hypotheses, persist/reload, geometry immutability.
