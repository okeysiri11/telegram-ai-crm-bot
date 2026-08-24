# STEP 29.10 RESULT — Odessa city navigation

Date: 2026-08-23

## Shipped

Map-style camera (left pan, right/modifier orbit, wheel zoom, damping,
polar + ground limits), animated «Общий вид», in-canvas 2D/3D without
remounting the model, whitelist hover, click/double-click/ESC selection,
object info panel actions, `?cityDebug=1`.

Geometry, packages, FBX/GLB, vertical Z, and calibration were not touched.

## Deferred

Weather, traffic, day/night, real building APIs, new meshes, GPS / STEP 30.
Safari visual sign-off of the metric city is still pending (STEP 29.9).

## Build / lint / tests

- `npx vitest run src/enterprise-city` — **311 passed / 1 skipped**
- `npx vite build` — **PASS**
- `/enterprise-city` on the running Vite server — **HTTP 200**

## Architectural decisions

Recorded in `docs/STEP_29_10_ODESSA_CITY_NAVIGATION.md`.
The interaction stack stays on `OdessaSceneController` + `interaction/`
(not a React-hook rewrite). 2D/3D is a camera pose, not a remount.

## Follow-ups

Manual WebGL pass in the browser: hover sea/ground stay unhighlighted,
double-click focus, home tween, 2–3 min camera move for leaks.
