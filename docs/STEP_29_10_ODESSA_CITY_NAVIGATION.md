# STEP 29.10 — Odessa 3D camera, hover, selection

Camera + navigation + hover + selection only.
Geometry, georeference, GPS, FBX/GLB pipeline, vertical Z, and building
heights are unchanged. STEP 30 is not started.

---

## Architectural decisions

1. **Extend the existing controller + `interaction/` modules.** No React
   hook rewrite of the scene. Camera pose helpers live in
   `cameraViewMode.ts`; pick whitelist in `pickFilter.ts`.
2. **Do not remount the city for 2D/3D.** In-canvas mode only tweens
   the same `PerspectiveCamera` and tightens polar limits. Page-level
   2D map remount is unchanged.
3. **Register-time whitelist, not per-frame material walks.** Sea,
   terrain, roads, vegetation, and city-scale merges never enter
   `PickRegistry`, so hover cannot paint them.
4. **minDistance stays 12 m**, not scaled by the ~84 km metric diagonal
   or by overview `near`. City → district → block → building zoom
   remains possible.

---

## Camera limits

| Parameter | Value |
|---|---|
| minDistance | 12 m |
| maxDistance | fit of city diagonal (unchanged helper) |
| minPolarAngle (3D) | 0.22 rad (~12.6° from nadir) |
| maxPolarAngle (3D) | π / 2.08 (~86.5°, never underground / flip) |
| min/maxPolarAngle (2D) | 0.02 … 0.28 rad (near top-down) |
| min height above city base | 4 m |
| damping | 0.085 |
| home / 2D–3D tween | 1100 ms |
| focus / double-click tween | 900 ms |

Mouse: left = pan, wheel = zoom, right (or Alt/Ctrl/Shift + left) = orbit.
Touch: one finger pan, two fingers dolly+rotate.

---

## Hover

Throttled `pointermove` at 55 ms. Candidates = whitelist only.
Highlight: steel emissive 0.07 + optional thin edges (skipped if the
mesh has > 8 000 vertices). Never a saturated green flood. Materials
are cloned only for the current hover/selection mesh.

## Selection

- Click building → select, right panel, subtle selected emissive 0.16
- Click empty / ESC → clear
- Double-click → keep selection, tween camera to the object AABB
- Panel: Приблизить / Добавить в избранное / Снять выбор

## Excluded from raycast

Name tokens: `base`, `plane`, `river(s)`, `road(s)`, `highway`, OSM
class names, `port` / `harbor` / `pier` / `dock`, `terrain` / `ground`
/ `sea` / `ocean`, vegetation tokens.

Material class: `WATER`, `ROAD`, `GROUND`, `VEGETATION`.

Size: footprint > 400 m or height < 2 m.

Water-like meshes (`isWaterLikeMesh`) are always skipped.

## Debug

`?cityDebug=1` shows FPS, camera, target, hover/select names and XYZ.
Hidden in the normal URL.

## Regression (code / architecture)

A–C geometry: this sprint does not touch packages, transforms, or Z.
D–E hover: sea/ground are not registered pickables.
F–K navigation / 2D3D / panel: covered by unit tests + in-scene buttons.
L memory: highlight clones are disposed on release; no per-frame
material walk.

## Tests / build

See sprint result after CI commands in this session.
