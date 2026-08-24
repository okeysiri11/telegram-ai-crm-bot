# STEP 29.1 — Odessa 3D interactive calibration

## Status

Shipped a 3-point interactive calibration workflow on top of the STEP 29 geospatial core. Authored calibration is stored in browser `localStorage` only. Source GLB/manifest files are never overwritten. STEP 30 was **not** started.

## CALIBRATION UI

Toolbar **Калибровка** opens a left-side panel: points A/B/C, GPS lat/lon, provisional/final residuals, save/reset, JSON export/import, temporary camera presets.

## POINT PICKING

**Добавить точку** enters a dedicated picking mode. Clicks raycast `odessaCityRoot` and store the exact `intersection.point` (world X/Y/Z). Object selection and hover highlight are paused while picking. Closing the panel restores normal picking.

## GPS INPUT

Manual WGS84 only. Invalid numbers / out-of-range lat/lon are rejected. Points closer than 20 m (GPS) or 2 world units (XZ) are rejected as duplicates. Far-from-Odessa values warn but can still be applied.

## CONTROL POINTS CURRENTLY

**0 in source code** (`AUTHORED_GEO_CONTROL_POINTS` remains empty). Runtime points exist only after the operator captures A/B/C and saves. Restored from `localStorage` on the next Odessa 3D load when the model fingerprint matches.

## SOLVER

Uniform similarity: translation + yaw + uniform scale. Two complete points → provisional. Three points → least-squares fit. City geometry is never deformed.

## AXIS INFERENCE

Eight Y-up ground mappings are scored; the lowest residual with positive scale wins. Rotation cannot absorb a reflection (east=+X / north=−Z vs identity).

## PROVISIONAL CALIBRATION

A+B complete → status **PROVISIONAL** in the panel. Overlays stay **off** until an acceptable 3-point solve is saved.

## INDEPENDENT VALIDATION

Point C is held out of the A+B solve; residual is reported in meters, then all three points are refit.

## PERSISTENCE

**Сохранить калибровку** writes control points, origin, translation, rotation, scale, axis mapping, quality, mean/max error, timestamp, version, fingerprint. Source: `AUTHORED_CONTROL_POINTS`. Confidence: `CALIBRATED`. Key: `ados.odessa3d.authored_calibration.v1`.

**Сбросить калибровку** requires confirmation and removes that key only.

## MODEL FINGERPRINT

Stable hash of manifest `cityId`, `version`, `packageFormat`, tile ids, stats, `cityBounds`. Mismatch → **CALIBRATION_MODEL_MISMATCH**, overlays off, operator must re-verify.

## GEOREFERENCE STATUS

Uncalibrated: **CALIBRATION_REQUIRED**. Saved + fingerprint match + revalidation: **READY_CALIBRATED** (STEP 29 overlays on). Fingerprint mismatch: **CALIBRATION_MODEL_MISMATCH**.

## SATELLITE REFERENCE

Architecture stub only (`SATELLITE_REFERENCE.provider = null`). No map SDK.

## VISUAL REGRESSION

This step does not change materials, lighting, water, LOD, GLB geometry, texture filtering, pixel ratio, antialiasing, fog, or the render pipeline. Calibration markers are a separate `MeshBasicMaterial` group, visible only while the panel is open.

## PERFORMANCE IMPACT

Picking is click-time raycast against the city root. Markers: 3 cones. No per-frame geo recompute.

## FILES CHANGED

- `src/web/src/enterprise-city/odessa3d/geospatial/*` (solver, store, session, UI, markers, fingerprint)
- `src/web/src/enterprise-city/odessa3d/odessaSceneController.ts`
- `src/web/src/enterprise-city/odessa3d/Odessa3DView.tsx`
- `src/web/src/index.css`

## TESTS

`calibrationWorkflow.test.ts` covers capture, GPS, duplicates, 2-point solve, axis inference, rotation/scale/translation, degenerate pairs, provisional, independent residual, least-squares, quality, save/load, mismatch, reset, JSON export/import, invalid JSON, round-trip.

## BUILD

`npm test -- src/enterprise-city` — **242 passed**. `npx vite build` — **PASS**.

## USER ACTION REQUIRED

See the chat report (Russian click-through).

## STEP 30 STARTED

NO
