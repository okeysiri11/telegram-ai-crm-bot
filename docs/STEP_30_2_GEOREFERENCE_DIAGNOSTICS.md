# STEP 30.2 — Diagnosable Odessa georeference

Date: 2026-08-23

STEP 31 was **not** started. No landmark GPS was invented. Scale was
**not** forced to 1. No magic offsets were added. The production
transform is **not** auto-changed from axis tests. A/B/C points are
**not** auto-removed. Model geometry, GLB/FBX, `odessa_metric`,
heights, footprints, coastline, water, materials, STEP 29 repairs,
and camera/navigation math were **not** modified.

Calibration is **not** claimed fixed. STEP 30.1 CHECK error (~36.6 m)
is still unexplained until a new A/B/C + independent CHECK dump is
evaluated.

---

## Status

`DIAGNOSTICS READY = YES`  
`RAW A/B/C PERSISTED = YES` (schema v3)  
`CALIBRATION FIXED = NO`  
`SAFE TO PERFORM REAL CALIBRATION = YES` — owner must reset, re-pick
A/B/C/CHECK, copy the V3 dump, and send it back.  
`STEP 31 = NOT STARTED`

---

## Architectural decisions

- Persist **raw observations** (world + GPS + `pickedAt` +
  `coordinateSpace = "world"` + model-root transform +
  `schemaVersion = 3`), not only the solved transform.
  Storage keys: `ados.odessa3d.georeference.v3`,
  `ados.odessa3d.georeference.observations.v3`. v2/v1 records still
  load; observations are synthesized from `controlPoints` when
  missing.
- Quality / ACCEPTABLE / GOOD uses **horizontal** X/Z vs GPS ENU.
  3D RMS/max stay as diagnostics so terrain Y cannot pass or fail
  a horizontal georeference.
- Pair scales and leave-one-out are **read-only**. Convention is
  always `WORLD_UNITS_PER_METER`. Package expected remains
  `1.0` meters per world unit and is **not** forced.
- CHECK never enters the solver. Pair-solvers (AB/AC/BC) also
  predict CHECK independently.
- Axis RMS is reported for all `HORIZONTAL_AXIS_CANDIDATES`
  (including swapped X/Z). Best mapping is not applied
  automatically.
- Picks stay `raycaster.intersectObject(...).point` in Three.js
  world space.

---

## Gate table

| Gate | Result |
| --- | --- |
| RAW OBSERVATIONS PERSIST | PASS |
| V2 → V3 MIGRATION | PASS |
| HORIZONTAL QUALITY METRIC | PASS |
| PAIR SCALE DIAGNOSTICS | PASS |
| LEAVE-ONE-OUT | PASS |
| CHECK EXCLUDED FROM SOLVER | PASS |
| SCALE FORENSICS (no force) | PASS |
| AXIS TEST (no auto-apply) | PASS |
| PICK = intersection.point WORLD | PASS |
| MODEL MODIFIED | NO |
| GLB MODIFIED | NO |
| STEP 31 | NOT STARTED |
| CALIBRATION CLAIMED FIXED | NO |

---

## Owner action required

1. Reload Odessa 3D.
2. Reset old calibration.
3. Pick A and enter GPS.
4. Pick B and enter GPS.
5. Pick C and enter GPS.
6. Press **Проверить**.
7. Pick independent CHECK and enter GPS.
8. Press **Проверить**.
9. Press **КОПИРОВАТЬ GEO ДИАГНОСТИКУ**.
10. Send the complete `=== GEOREFERENCE DIAGNOSTIC V3 ===` block
    back for evaluation.
