# STEP 20 — Odessa 3D Water Artifacts + Close-Range Camera Navigation

## Shipped

- Runtime water classification + duplicate sea-surface guard (`waterSurfaceGuard.ts`)
- Stable Water material (no mirror specular): metalness 0, roughness ≥ 0.68, FrontSide, opaque, depthWrite
- Coplanar river/sea z-fight: polygonOffset + renderOrder on protected rivers (geometry not deleted)
- Camera near/far from current city bounds (`computeCameraClipRange`) — no 0.001 near, no logarithmicDepthBuffer
- Distance-aware OrbitControls pan (far 1.0x → near 2–4x, clamped)
- Screen-space panning kept (city-map drag)
- `zoomToCursor` enabled (configurable) so zoom/orbit target follows the inspected area
- Reset Camera restores overview target at city center
- Dev-only **WATER DEBUG** toggle (names, Y, bounds, material, renderOrder, diagnostic colors)

## WATER ROOT CAUSE

Inspected all 45 GLBs (JSON + world AABB). Three meshes share material `Water`:

| Node | File | World AABB (XZ) | Y | verts |
|---|---|---|---|---|
| WEB_water | TILE_04_00_REST_BATCH_07 | X[-324,304] Z[-658,294] | ~0 | 9564 |
| WEB_bay | TILE_05_00 | X[-105,318] Z[-180,307] | ~0 | 2898 |
| WEB_rivers | TILE_03_00 | X[-418,197] Z[-280,331] | ±0.01 | 13836 |

Authored Water PBR: **metalness = 0.5, roughness = 0, doubleSided, opaque**. Combined with a warm DirectionalLight and ACES tone mapping this produces moving brown/specular streaks at medium/far distance (specular aliasing). WEB_bay is 94% contained in WEB_water at the same Y — true duplicate sea surface / z-fighting. Artifact disappearing when close matches both depth precision and specular aliasing.

## WATER MESH COUNT

- Classified water-like meshes: **3**
- Kept visible: **2** (`WEB_water`, `WEB_rivers`)
- Hidden as duplicate: **1** (`WEB_bay`)
- Not classified (structures): water_tower, wastewater, water_well, breakwater

## DUPLICATES FOUND

`WEB_bay` ≡ overlapping sea/bay of `WEB_water` (containment ≈ 0.94, same Y, same Water material). Hidden at runtime. GLB geometry is not deleted.

`WEB_rivers` kept (protected river category) even though its AABB overlaps the sea. polygonOffset applied where coplanar with sea.

## MATERIAL CHANGES (runtime only)

For Water-like materials:

- metalness = 0
- roughness = max(authored, 0.68)
- envMap = null / envMapIntensity = 0
- transparent = false, opacity = 1
- depthWrite = true, depthTest = true
- side = FrontSide
- no city-wide lighting dimming

## DEPTH / CAMERA CHANGES

`near`/`far` computed from live manifest + loaded bounds. Logarithmic depth buffer **not** enabled.

## NEAR / FAR VALUES (current Odessa cityBounds)

- size ≈ 735 × 2 × 1048 m, diagonal ≈ 1280 m
- **near ≈ 1.28** (clamped to 0.5–2.0)
- **far ≈ 7053** (orbit margin + city diagonal; quality `cameraFarCap` still applied)
- previous: near ≈ 0.52, far up to 16000–20000 (ratio ~30k → now ~5.5k)

## PAN ROOT CAUSE

OrbitControls pan scales with camera–target distance. Close zoom made Shift+drag microscopic in world units even though screen-space panning was already on.

## PAN SCALING STRATEGY

`effectivePanSpeed = basePanSpeed (0.85) * distanceCompensation * viewportCompensation`

- far / overview: **1.0x**
- district / medium: **1.2–1.5x**
- near / blocks: **2–4x**
- very near: **capped at 4x** (never infinite)
- Updates on control start/change/end only (not a full mesh scan)

## TRACKPAD RESULT

- Shift + drag → pan (OrbitControls default)
- Two-finger scroll → zoom/dolly
- Drag without Shift → orbit
- Touch: ONE rotate, TWO DOLLY_PAN
- Pan multiplier is clamped to prevent jumps

## SCREEN SPACE PANNING STATUS

**Kept `screenSpacePanning = true`.** City-map movement stays parallel to the view. World-up pan is worse for a mostly-flat city.

## TARGET MANAGEMENT STATUS

- Reset Camera / fitCameraToOdessa restores target to **city center**
- Double-click focus still moves target to the hit point
- Normal pan/orbit does **not** reset target
- `zoomToCursor = true` by default (configurable via `setZoomTowardPointer`) so zooming over a district pulls the orbit pivot toward the pointer

## TEST RESULTS

`npm test -- src/enterprise-city` — **86 passed** (8 files)

Coverage added: water classification, duplicate guard, non-water preservation, clip range, pan scale + clamp, reset target = city center, 2D→3D→2D view-mode roundtrip.

## BUILD RESULT

`npx vite build` — **PASS** (14.33s). Pre-existing chunk-size warnings only.

## DEV SERVER URL

http://localhost:5180/enterprise-city → **3D Одесса** → wait for ODESSA READY

Debug (owner overlay): **WATER DEBUG**

## REMAINING ISSUES

- `WEB_rivers` still overlaps the sea in AABB; inland ribbons cannot be split from coastal overlap without editing source geometry (out of scope).
- Mild specular from ACES + a large water plane can remain at grazing angles; not the previous brown strobing.
- `zoomToCursor` can be turned off if a given input device feels unstable.

## Architectural decisions

- **Do not delete GLB/Blender water.** Hide true duplicate sea surfaces only.
- **Fix water material before city lighting.**
- **logarithmicDepthBuffer stays false.** Clip range + duplicate guard are sufficient.
- No geoTransform / tile / manifest / 2D map changes.

## Deferred

- Animated / screen-space water reflections
- Logarithmic depth buffer
- STEP 21
