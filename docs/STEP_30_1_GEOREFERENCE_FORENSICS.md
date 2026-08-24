# STEP 30.1 — Georeference forensics (read-only)

Date: 2026-08-23

Production calibration, GLB/FBX, geometry, camera, UI, quality
thresholds, and solver code were **not** changed. STEP 31 was **not**
started. CHECK was **not** added to the solver.

---

## 1. Saved A/B/C — not on disk, not in localStorage

Authoritative store:

- key: `ados.odessa3d.georeference.v2`
- fallback: `ados.odessa3d.authored_calibration.v1`
- file: `src/web/src/enterprise-city/odessa3d/geospatial/calibrationStore.ts`

Live origin `http://127.94.0.1:5180` was read. Both keys are **null**.
`odessa3d.package` is also unset (defaults to `REBUILT_METRIC`).

No labels/names are stored on control points (only `id` / `label` A/B/C).

**Implication:** the UI numbers below are from an **in-session wizard
preview** (`evaluateCalibrationDraft` + `evaluateCheckPoint`), not a
reloaded `READY_CALIBRATED` record. Per-point A/B/C world+GPS cannot
be reconstructed from mean/max residuals.

Observed session (operator report):

| Quantity | Value |
| --- | --- |
| CONTROL FIT ERROR (mean) | 6.56 m |
| Maximum control error | 8.77 m |
| Scale (world units / meter) | 1.4475 |
| Rotation | 0.0043 rad (0.246°) |
| Quality | ACCEPTABLE |
| CHECK world | −1935.01, 20.66, 15514.82 |
| CHECK entered GPS | 46.386267, 30.705832 |
| CHECK predicted GPS | 46.386292, 30.705357 |
| CHECK REAL-WORLD ERROR | 36.55 m |

---

## 2. Solver in production

| Item | Value |
| --- | --- |
| File | `src/web/src/enterprise-city/odessa3d/geospatial/geoCalibration.ts` |
| 3-point / persist path | `solveCalibrationWithAxisInference` → `solveCalibrationFromControlPoints` |
| Preview | `evaluateCalibrationDraft` in `calibrationSession.ts` |
| CHECK (hold-out) | `evaluateCheckPoint` — `includedInSolver: false` |
| Runtime restore | `resolveOdessaCalibration` (re-solves from saved points; does not trust stored yaw/scale blindly) |

### Mathematical model

2D similarity on the ground plane only:

1. `origin` = mean WGS84 of the fit points (not `ODESSA_GEO_ORIGIN`).
2. `worldOrigin` = mean world XYZ of the fit points (Y is averaged, not solved).
3. GPS → ENU at **that** `origin` (`wgs84ToLocalMeters`).
4. World ΔXZ mapped to east/north via `axisMapping`.
5. Kabsch-like 2D: `rotation = atan2(cross, dot)`, uniform
   `worldPerMeter = rotatedDot / srcVar`, `metersPerWorldUnit = 1/worldPerMeter`.
6. Negative scale is rejected (`reflected_scale`). No shear. No Y scale.

### Horizontal axes

Candidates: `HORIZONTAL_AXIS_CANDIDATES` (8 mappings). Best mean residual
wins. Identity is `E→x N→z U→y`. Uncalibrated legacy assumption is
`E→x N→−z U→y`.

CHECK vs city-center ENU matches **E=+X, N=−Z** to ~20 m if world
origin is treated as (0,0,0). Rotation 0.25° cannot flip north.
**Inferred current mapping: `E→x N→−z U→y`.** Not proven without A/B/C.

### ODESSA_GEO_ORIGIN

`46.4825, 30.7233` — ENU **math** origin / GPS range check / OSM helper.
The solver’s `calibration.origin` is the **mean of A/B/C GPS**, not this
constant. World `(0,0,0)` is not locked to it.

### WGS84 ↔ ENU

`localMeters.ts`:

- `east = Δlon * metersPerDegreeLongitude(origin.lat)` (WGS84 ellipsoid, **latitude-dependent**)
- `north = Δlat * metersPerDegreeLatitude(origin.lat)`
- `up = Δaltitude`

Inverse is the same scales. **Yes, cos(latitude) is applied.**

### Altitude / world Y

- Horizontal solve: **Y is not used** (only XZ after axis map).
- Control residual (`solveCalibrationFromControlPoints`):
  `hypot(dx,dy,dz) * metersPerWorldUnit` — **includes Y**.
- CHECK residual (`evaluateCheckPoint`):
  horizontal ENU only — **excludes Y**.

These two numbers are **not the same metric**. Do not compare 6.56 m
CONTROL FIT to 36.55 m CHECK as if they were.

---

## 3. Per-point A/B/C residuals

**Not computable.** Points are not in storage. Only mean 6.56 / max 8.77.

---

## 4–5. Leave-one-out and CHECK vs two-point solves

**Not computable** without A/B/C. CHECK was not used in the 3-point fit
(code path confirmed).

Independent verification of the reported CHECK GPS pair, using the
same ENU formulas at `ODESSA_ENU_ORIGIN`:

- Δeast ≈ −36.47 m
- Δnorth ≈ +2.78 m
- horiz ≈ **36.58 m** (UI 36.55 m — rounding)

CHECK error is **almost purely east–west**.

---

## 6. Scale pairs

**Not computable** without A/B/C.

Package claim (`REBUILT_METRIC`): `worldUnitsPerMeter = 1`.
Solver scale: **1.4475** world units per meter (1 m ≈ 0.691 world units).
That is a **44.75%** disagreement with the package note
“1 world unit = 1 meter”. Either the geographic correspondences are
stretched, or the model is not 1:1 with WGS84.

CHECK world XZ from (0,0) × 0.6908 ≈ 10.80 km.
CHECK GPS from city center ≈ 10.78 km (1.34 km west, 10.70 km south).
Distance magnitude is consistent with scale 1.4475 **if** world origin
is near (0,0,0) and mapping is N=−Z.

---

## 7. Handedness (diagnostic only — production transform untouched)

From CHECK + reported scale, vs city-center ENU of entered GPS:

| Mapping | Implied ENU (world×mpu, origin 0) | vs GPS ENU (−1341, −10697) |
| --- | --- | --- |
| X→E, Z→N | (−1337, +10718) | north sign **wrong** |
| X→E, Z→−N | (−1337, −10718) | **closest** (~20 m N) |
| X→N, Z→E | (+10718, −1337) | swapped |
| −X→N, Z→E | — | swapped |

RMS per mapping on A/B/C was **not** recomputed (no points).

---

## 8. Cause checklist

| Hypothesis | Evidence |
| --- | --- |
| Wrong A/B/C correspondence | Possible. 3-point fit 6.6 m vs hold-out 36.6 m is classic overfit / one bad pair. Cannot name which point. |
| Wrong CHECK | Possible but GPS/world distance magnitude matches the fitted scale. Error is 0.34% of the ~10.8 km baseline — large for a building, small as a similarity leftover. |
| Axis mapping | Inferred N=−Z, E=+X. Rotation ~0. Production infers this; not a sign flip bug at 0.25°. |
| Rotation sign | 0.0043 rad. Not a 180° error. |
| Scale | 1.4475 vs package 1.0 is a first-class finding. Pair-to-pair scale unknown. |
| Translation | `worldOrigin` = mean of A/B/C. CHECK vs (0,0,0) is only an approximation. |
| WGS84↔ENU / cos(lat) | Used correctly in the **new** solver. CHECK UI error reproduces to 0.03 m. |
| Wrong ODESSA_GEO_ORIGIN as model lock | Origin is math-only. Solver uses mean(A,B,C). |
| Legacy `GeoTransform` | `geoTransform.ts`: fixed 111000 / **75000** deg scales, N=−Z. Used for **tile streaming fallback only**, not A/B/C/CHECK. ~2.3% lon-scale error vs ellipsoid. Different code path. |
| Local vs world pick | `raycastWorldHit` returns `hit.point` (Three.js **world**). `odessaCityRoot` is not translated/scaled. Solver consumes that XYZ. **Same space.** Markers are placed at the same world XYZ. |
| Normalization / recenter | Metric rebuild is translation×100 / scale→1 on nodes; buffers unchanged. Picking is post-assembly world. No extra recenter in the solver. |
| CONTROL vs CHECK metric mix | CONTROL includes unfitted Y; CHECK is horizontal. Heights on A/B/C can inflate 6.56 / 8.77 without hurting horizontal CHECK. |

CHECK GPS 46.386267, 30.705832 is ~10.7 km south / 1.3 km west of the
published city center. No project metadata proves which real object
that is. Do not auto-identify it.

---

## Recommended next action

1. If the wizard session is still open: copy A/B/C world XYZ + GPS
   (`?cityDebug=1` session dump) and re-run this forensic.
2. If the tab remounted: re-pick A/B/C (storage was empty — nothing
   to restore).
3. Do not lower ACCEPTABLE/GOOD thresholds to hide 36 m CHECK.
4. Do not feed CHECK into the solver.
5. Re-survey with far-apart, same-class features (building corners /
   pier ends), then compare pair scales AB/AC/BC.

STEP 31: do not start.
