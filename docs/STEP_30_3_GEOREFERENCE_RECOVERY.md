# STEP 30.3 — Historical A/B/C recovery and automated replay

Date: 2026-08-23

STEP 31 was **not** started. No A/B/C coordinates were invented.
Scale was **not** forced to 1. Quality thresholds were **not** relaxed.
CHECK was **not** added to the solver. Geometry / GLB / `odessa_metric`
were **not** modified.

---

## Recovery

| Point | Status | Source |
| --- | --- | --- |
| A world + GPS | **MISSING** | — |
| B world + GPS | **MISSING** | — |
| C world + GPS | **MISSING** | — |
| CHECK world | recovered | operator STEP 30.1 report; `docs/STEP_30_1_GEOREFERENCE_FORENSICS.md` |
| CHECK GPS | recovered | same |

Safari had two live tabs on `http://127.94.0.1:5180/enterprise-city`.
Apple Events JavaScript is disabled, so those tabs’ `localStorage`
could not be read. Safari WebsiteData is TCC-blocked from this
environment.

`AUTHORED_GEO_CONTROL_POINTS` is an empty array by design.

---

## Sources searched

- `ados.odessa3d.georeference.v3` / `.v2` / `authored_calibration.v1` /
  `observations.v3` in repo, git history, Chrome LevelDB, Cursor
  LevelDB — **not present**
- `calibrationStore.ts`, `calibrationSession.ts`, `geoCalibration.ts`,
  `worldTransform.ts`, `localMeters.ts`, `odessaSceneController.ts`,
  `odessaPackage.ts`, both `odessa_manifest.json`
- `docs/` (STEP 29 / 30 / 30.1 / 30.2)
- test fixtures (synthetic only; not user points)
- Downloads / Desktop `*geo*` / `*calibrat*` JSON — none
- agent transcript — CHECK only; A/B/C never logged
- live origin 5180 — page is up; storage not readable from here

---

## Why solver replay did not run

Phase 2 stop: A, B, and C cannot be recovered exactly.
Replaying `solveCalibrationWithAxisInference` would require
synthesized controls. That is forbidden.

The previous ~36.6 m CHECK error **cannot** be attributed to a named
control point, scale, axis, or solver defect without A/B/C.

`ROOT_CAUSE = F` (insufficient historical data).

---

## Next action

Owner must copy `=== GEOREFERENCE DIAGNOSTIC V3 ===` from the wizard
(STEP 30.2) or enable Safari “Allow JavaScript from Apple Events”
so the live tab storage can be read. Then STEP 30.3 replay can resume.
