# STEP 30.1 — Odessa georeference control-point workflow

Date: 2026-08-23

STEP 31 was **not** started. No landmark GPS was invented. Model
geometry, GLB/FBX, `odessa_metric`, heights, footprints, coastline,
water, materials, STEP 29 repairs, and camera/navigation math were
**not** modified.

---

## Status

`CALIBRATION SYSTEM READY = YES`  
`REAL CALIBRATION REQUIRED = YES`  
`SAFE TO PERFORM REAL CALIBRATION = YES` — owner can pick A/B/C in
the wizard and enter real WGS84 without DevTools.  
`MANUAL ACTION REQUIRED = YES` — select real A/B/C correspondence.

---

## Architectural decisions

- Owner UI is `CalibrationWizard` (4 steps). The technical
  `CalibrationPanel` stays behind `?cityDebug=1` only.
- Control points store **raycast `intersection.point`**, never mesh
  origin / pivot / bounding-box center / building centroid.
- Camera does **not** jump after a pick. Orbit / pan / zoom stay on
  the existing STEP 29.10 navigation system.
- Enterprise City 2D uses a 0–100 plane (`planeToGeo`) and is **not**
  WGS84. GPS is never read from that map.
- 2D-assisted workflow is sequential: 3D pick → OpenStreetMap Odessa
  helper (`Найти координаты` / `Указать эту точку на 2D`) → paste
  `lat, lon`. The helper does not guess coordinates.
- Split 3D+map layout was **not** added: it would rewrite the city
  shell. Sequential wizard is the supported path.
- CHECK is a fourth hold-out point. It is never added to the solver.
  CONTROL FIT ERROR and CHECK REAL-WORLD ERROR are shown separately.

---

## Gate table

| Gate | Result |
| --- | --- |
| CALIBRATION WIZARD | PASS |
| 3D POINT PICK | PASS |
| 2D ASSISTED PICK | PASS (OSM helper + paste; city plane is not WGS84) |
| GPS INPUT | PASS |
| A/B/C | PASS |
| SPATIAL VALIDATION | PASS |
| SOLVER PREVIEW | PASS |
| CHECK POINT | PASS |
| SAVE/LOAD | PASS |
| RESET | PASS |
| MODEL MODIFIED | NO |
| GLB MODIFIED | NO |
| TESTS | 339 passed / 1 skipped / 0 failed |
| BUILD | PASS |
| MANUAL ACTION REQUIRED | YES — select real A/B/C correspondence |
| SAFE TO PERFORM REAL CALIBRATION | YES |

---

## Owner workflow

1. Open Odessa 3D and click **Геопривязка**.
2. Step 1/4: **Выбрать точку A**, click a recognizable surface on the
   model. Marker **A** appears. Enter or paste WGS84, then
   **Применить GPS**. Use **Найти координаты** to open an Odessa map
   and copy GPS of the same place.
3. Repeat for B and C. Choose points far apart (pier end, large
   building corner, major road crossing). Avoid sea center, trees,
   tiny or unknown objects.
4. Step 4/4: read **ПРЕДВАРИТЕЛЬНЫЙ РЕЗУЛЬТАТ**. Optionally pick
   **CHECK**, enter its GPS, click **Проверить**.
5. If quality is acceptable: **Сохранить геопривязку** →
   `READY_CALIBRATED`. Reload restores it when the model fingerprint
   matches.
6. **Сбросить геопривязку** asks for confirmation and deletes
   calibration v2 only. The model is unchanged.

---

## Debug

`?cityDebug=1` shows A/B/C world+GPS, AB/AC/BC, triangle area, yaw,
scale, translation, residuals, CHECK predicted/actual/error, plus the
technical panel.

---

## Regression

cameraNavigation, interaction, Odessa3DView, hover, selection,
double-click, home, 2D/3D, materials, water, and render stability
were not rewritten. Geometry was not touched.

---

## STOP

STEP 30.1 complete. Do not start STEP 31 until a human has surveyed
real A/B/C correspondence.
