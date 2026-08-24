# STEP 29.2 — Odessa 3D render stability

## Status

Odessa 3D load was already working. Orbit/pan/zoom produced flashing, striping, washout, and angle-dependent lighting. This step fixes **render stability only**. GLB coordinates, STEP 29 geospatial core, and STEP 29.1 A/B/C calibration are unchanged. STEP 30 was **not** started.

Dev diagnostics (when **Диагностика** is on) now include isolation toggles:

- Base model only
- Disable water
- Disable overlays
- Neutral material diagnostic

and counters: city-root instances, mesh counts, transparent / `depthWrite=false` materials, camera near/far/ratio, pixel ratio, draw calls, triangles.

## ROOT CAUSE

**Wrong texture color space on data maps.** Color maps (`map`, `emissiveMap`) must be sRGB; normal / roughness / metalness / AO maps must stay linear. Treating every texture as sRGB made lighting and albedo swing with camera angle (washout, flicker, “different city from a new azimuth”).

## SECONDARY CAUSES

1. **Depth precision** — far plane was ~4× city diagonal while near could sit too low; Safari/Intel often drop to 16-bit depth when a stencil buffer is requested, which shows up as swimming stripes on coplanar ground/water.
2. **Water roughness tied to camera distance** — sea tint/roughness lerped while orbiting, so water and adjacent terrain changed appearance with zoom.
3. **Non-idempotent texture filter updates** — `needsUpdate` was set even when minFilter/anisotropy were already correct.
4. **Coplanar overlays** — water, debug grid, selection helpers can z-fight with the city surface if isolation is off (water already uses polygonOffset; overlays can be hidden diagnostically).

Duplicate `odessaCityRoot` mount was **not** the live bug (React remount disposes the previous controller). A parent guard was added anyway.

## CITY ROOT INSTANCES

**1** (named `odessaCityRoot`). `scene.add` is skipped if the group already has a parent. Diagnostics count named instances.

## CAMERA NEAR

**~2.56** world units from Odessa bounds (clamped to `[1, 4]`). Adaptive clip may raise near slightly when zoomed in, with hysteresis so the projection does not chatter every frame.

## CAMERA FAR

**~3328** world units (`max(diagonal × 2.6, maxDim × 2.8, 2200)`), still capped by the quality profile far cap.

## FAR/NEAR RATIO

**~1300** at overview (was much worse with 4× diagonal far and a tiny near). Logarithmic depth remains **off**.

## Z-FIGHTING

Mitigated: tighter clip, **stencil: false** (24-bit depth on Safari/Intel), water `polygonOffset`, duplicate-water guard unchanged. Overlays can be isolated; city mesh coordinates are not offset (picking/calibration still hit the real GLB).

## TEXTURE FILTERING

Idempotent: `LinearMipmapLinearFilter` + `generateMipmaps` + quality anisotropy, `needsUpdate` only when a parameter actually changes. No texture replacement, no global blur, no upscaling.

## MATERIAL STABILITY

Color-space fix is marked on `material.userData` and will not re-run. Urban visual pass remains once-per-material. Water roughness is frozen to the far value. Neutral diagnostic swaps a shared Lambert material and restores originals.

## WATER/OVERLAY INTERFERENCE

Possible contributor (coplanar sea vs terrain). Frozen roughness removes orbit-dependent retint. Dev toggles can hide water or overlays without deleting them.

## SAFARI STATUS

Renderer: `stencil: false`, `logarithmicDepthBuffer: false`, antialias follows quality profile, pixel ratio still clamped (LOW 1 / MEDIUM 1.25 / HIGH 1.5). Do not raise DPR further on Retina Safari.

## VISUAL TOP-DOWN / 45° / LOW / ZOOM

Engineering fixes are in the runtime path. In-agent Safari orbit was **not** captured (no browser automation in this session). Re-check in Safari at `http://127.94.0.1:5180/enterprise-city` → **3D Одесса**, orbit top-down / 45° / low oblique / zoom in–out. Neutral-material toggle: if striping remains, it is depth/geometry; if it disappears, leftover texture/light issues.

Do **not** capture A/B/C during that check.

## TESTS

**248 passed** (`npm test -- src/enterprise-city`). Baseline STEP 29.1 was 242. Added coverage for single city-root, idempotent color space, clip range, Safari renderer options, isolation restore.

## BUILD

**PASS** (`npx vite build` in `src/web`).

## FILES CHANGED

- `src/web/src/enterprise-city/odessa3d/renderStability.ts` (new)
- `src/web/src/enterprise-city/odessa3d/renderStability.test.ts` (new)
- `src/web/src/enterprise-city/odessa3d/odessaSceneController.ts`
- `src/web/src/enterprise-city/odessa3d/cityAssembly.ts`
- `src/web/src/enterprise-city/odessa3d/cameraNavigation.ts`
- `src/web/src/enterprise-city/odessa3d/cameraNavigation.test.ts`
- `src/web/src/enterprise-city/odessa3d/cityAssembly.test.ts`
- `src/web/src/enterprise-city/odessa3d/scenePrep.ts`
- `src/web/src/enterprise-city/odessa3d/odessaPerformance.ts`
- `src/web/src/enterprise-city/odessa3d/environment/waterEnvironment.ts`
- `src/web/src/enterprise-city/odessa3d/Odessa3DView.tsx`
- `src/web/src/enterprise-city/odessa3d/Odessa3DView.test.tsx`
- `src/web/src/enterprise-city/odessa3d/types.ts`
- `docs/STEP_29_2_ODESSA_3D_RENDER_STABILITY_RESULT.md`

## CALIBRATION SYSTEM PRESERVED

**YES.** No edits to STEP 29 solver/ENU/world transform, STEP 29.1 panel/session/store/fingerprint, GPS, localStorage, 2D/3D bridge, picking world points, or CRM.

## SAFE TO CALIBRATE

**YES** — after a short Safari orbit confirms flashing/stripes are gone. Do not start STEP 30. Do not capture A/B/C until that visual check.

## STEP 30 STARTED

**NO**
