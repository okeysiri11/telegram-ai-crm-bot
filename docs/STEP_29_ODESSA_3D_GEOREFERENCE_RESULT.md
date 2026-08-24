# STEP 29 — Odessa 3D georeference core

## Status

Shipped the WGS84 ↔ local-meters ↔ Three.js world architecture. The live Odessa GLB package is **not** georeferenced. Overlays stay off. Status is **CALIBRATION_REQUIRED**. No guessed alignment. STEP 30 was **not** started.

## EXISTING CRS AUDIT

| Item | Finding |
|---|---|
| EXISTING 2D CRS | Enterprise City plane **0–100**. Not WGS84. Documented in `CITY_LIVING_ECONOMY.md` as narrative “Digital Odessa”, not GIS. |
| EXISTING ODESSA MAP CENTER | `ODESSA_CITY` / manifest `46.4825, 30.7233` — labeled **“Approximate city center”**. |
| EXISTING BOUNDS | Manifest `cityBounds`: X −418…318, Z −389…658, Y −0.16…1.99 (authored ground envelope). 2D map is 0–100. |
| EXISTING 3D WORLD AXES | Blender export: `height_axis: Y`, `map_plane: [X,Z]`. `blenderBoundsToCity` maps Blender Y→Three Z, Z→Y. Three.js Y-up. Uncalibrated `GeoTransform` assumed east=+X, north=−Z — **unproven**. |
| MODEL WORLD BOUNDS | ~735 × 1048 world units on XZ. |
| MODEL UNIT SCALE | **Unproven.** Span looks meter-like; no metadata says 1 unit = 1 m. Authored Y extent ~2 is ground envelope, not building height. |
| MODEL ORIGIN | World (0,0,0) is **not** proven to be the WGS84 origin. Bounds are offset (center ≈ X −50, Z +134). |
| AVAILABLE GEO METADATA | Manifest `geoTransform.originLat/Lng` + `calibrated: false`. No EPSG, no control points, no rotation, no scale. `planeToGeo` is a fictional 2D-twin delta. |
| CALIBRATION DATA FOUND | **None that can bind the GLB to WGS84.** |

Streaming already uses `centerScene` (world XZ), not geo. Legacy `GeoTransform` remains a fallback only.

## GEOREFERENCE STATUS

**CALIBRATION_REQUIRED**

## CALIBRATION SOURCE

none (authored control-point table is empty)

## CONFIDENCE

UNAVAILABLE

## WGS84 ↔ LOCAL

Local tangent ENU meters around the published approximate Odessa center. Degrees are never treated as meters. Round-trip city-scale error **< 0.15 m** in tests.

## LOCAL ↔ WORLD

Implemented (`geoToWorld` / `worldToGeo`) with rotation, uniform scale, axis mapping, altitude. **Not applied at runtime** until calibration is READY.

## ROUND TRIP ERROR

ENU math: < 0.15 m. Calibrated world path (synthetic): < 0.05 world units. Live model: **N/A** (no calibration).

## CONTROL POINTS

**0**

## MEAN ERROR / MAX ERROR

null / null

## GEO BOUNDS

Not computed (requires READY calibration).

## ENTERPRISE ANCHORS

- Catalog buildings use `planeToGeo` (stamps `x/y`) → **rejected** as 3D WGS84. Never invented.
- `ODESSA_CITY` marker is pure lat/lng (approximate center) → **1 data POI**, not rendered.
- Rendered 3D markers: **0**

**BOUND (geo):** 0 buildings  
**UNBOUND (geo):** all 3D pickables + all catalog buildings

## SELECTED POINT GEO

Hidden unless READY. Click point is stored; conversion returns null today. UI will show “Координаты точки” (not an address) only after calibration.

## 2D/3D BRIDGE

`geoSelectionBridge` shares entity id (`city_building_*`) between 2D select and 3D select. No 2D map rewrite. Geographic payload is null until READY.

## PERFORMANCE IMPACT

Calibration resolved once at mount. Anchor worlds cached. No per-frame geo recompute. Marker scale updates only if overlays are on (they are not). STEP 20–28 paths unchanged.

## FILES CHANGED

- `src/web/src/enterprise-city/odessa3d/geospatial/*` (new core)
- `odessaSceneController.ts`, `Odessa3DView.tsx`, `OdessaObjectPanel.tsx`, `types.ts`, `index.ts`
- `geoTransform.ts` (comment: not authoritative)
- `EnterpriseCityPage.tsx` (2D writes selection bridge)
- `docs/STEP_29_ODESSA_3D_GEOREFERENCE_RESULT.md`

## TESTS

`npm test -- src/enterprise-city` — **219 passed** (geospatial 20).

## BUILD

`npx vite build` — **PASS**.

## CALIBRATION REQUIRED: YES

Provide, at minimum:

1. **Control point A** — a recognizable spot on the model with world `(X, Y, Z)` and a measured WGS84 `(lat, lon)`.
2. **Control point B** — a second point **hundreds of meters** away (scale + yaw).
3. **Control point C** (recommended) — residual validation.
4. Confirmation of **axes** (is +X east? is +Z south, as the old uncalibrated GeoTransform assumed?).
5. Confirmation of **units** (is 1 world unit 1 meter?).

Put them in `odessa3d/geospatial/geoCalibration.ts` → `AUTHORED_GEO_CONTROL_POINTS`. Do not guess.

## KNOWN LIMITS

- Local tangent ENU, not UTM / full GIS.
- No terrain DEM; altitude is optional and not claimed as ground elevation.
- Approximate city-center lat/lng is an ENU origin only, not a model georeference.
- Geo overlays, click WGS84, camera geo, and the metric grid stay disabled until READY.
- Safari live mesh/geo counts were not re-measured in this session; 3D load/pick paths were not rewritten.

## STEP 30 STARTED: NO
