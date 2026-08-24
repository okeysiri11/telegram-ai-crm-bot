# STEP 30 — Odessa 3D georeference calibration result

Date: 2026-08-23

Geometry, `odessa_metric`, FBX/GLB, vertical Z, and STEP 29.x rebuild
paths were **not** modified. No A/B/C GPS landmarks were invented.
STEP 31 was **not** started.

---

## PREFLIGHT

**PASS** (architecture / existing 29.10 camera+interaction tests).
Live Safari visual of the metric city was not re-run in this session.
If a needle forest or z-fighting regression appears in Safari, treat
this gate as failed and do not apply a saved calibration.

`STEP30_PREFLIGHT = PASS`

## MODEL GEOMETRY MODIFIED

**NO**

## GLB MODIFIED

**NO**

## Architecture (source of truth)

```
WGS84 lat/lon
    ↕  local tangent ENU (ODESSA_GEO_ORIGIN ≈ 46.4825, 30.7233)
    ↕  rigid/similarity world↔ENU (translation XZ + yaw + uniform horizontal scale)
WORLD XYZ (Three.js, Y-up)
```

`ODESSA_GEO_ORIGIN` is a **math** origin only. World `(0,0,0)` is **not**
assumed to be that point.

Existing STEP 29 modules were extended (`geospatial/*`), not rewritten.

## CALIBRATION UI

**PASS** — toolbar «Геопривязка», compact left drawer, A/B/C capture,
GPS apply, clear/delete, distances, solver residuals, save v2,
explicit POOR confirm.

## CONTROL POINTS

A/B/C slots exist. **0 authored GPS points.** User must survey them.

## SOLVER

**PASS** — A+B provisional, A+B+C least squares, axis candidates,
no reflection-as-scale, Y/height not calibrated.

Quality: EXCELLENT &lt; 2 m · GOOD 2–5 m · ACCEPTABLE 5–15 m · POOR &gt; 15 m.

## WGS84 ↔ ENU

**PASS** (existing city-scale round-trip &lt; 0.15 m)

## WORLD ↔ GEO

**PASS** when READY; disabled before READY.

## CAMERA GEO

**PASS** — throttled via `?cityDebug=1` poll (250 ms). Hidden until READY.

## CLICK GEO

**PASS** — only after READY_*. Before: «Геопривязка не выполнена».

## 2D→3D / 3D→2D

**PASS** — `geoSelectionBridge.requestShowIn3d/2d`. 2D marker shows WGS84
text. Does **not** invent 0–100 plane GPS from `planeToGeo`.

## MODEL FINGERPRINT

**PASS** — includes package id + manifest tiles/bounds. Mismatch →
`CALIBRATION_MODEL_MISMATCH`.

## Storage

`ados.odessa3d.georeference.v2` (reads v1 as fallback). Never writes GLB.

## CALIBRATION PERFORMED

**NO**

## CALIBRATION SYSTEM READY

**YES**

## REAL CALIBRATION REQUIRED

**YES** — wait for surveyed A/B/C world+WGS84 pairs.

## VISUAL REGRESSION

**NEEDS MANUAL SAFARI CHECK**

Calibration overlays are off by default. City materials/geometry
untouched.

## SAFE FOR STEP 31

**NO** until a real 3-point calibration is authored and Safari visual
PASS is recorded.

## TESTS

**316 passed / 1 skipped / 0 failed** (`npx vitest run src/enterprise-city`)

## BUILD

**PASS** (`npx vite build`)
