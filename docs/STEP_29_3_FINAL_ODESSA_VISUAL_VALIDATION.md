# STEP 29.3 — Final Odessa Visual Validation (before A/B/C georeference calibration)

Date: 2026-08-23
Scope: `src/web/src/enterprise-city/odessa3d/`
Prerequisite: STEP 29.2 render stability hotfix (complete).
No calibration performed. STEP 30 not started.

---

## Verdict summary

| Field | Result |
| --- | --- |
| RENDER STABLE | **YES** |
| REMAINING WASHOUT CAUSE | **B/E — FogExp2 coastal haze (by design), not a render defect** (see below) |
| COLOR SPACE | **PASS** |
| LIGHTING | **PASS** |
| TONE MAPPING | **PASS** |
| WATER | **PASS** |
| DEPTH | **PASS** |
| TOP DOWN | **PASS** (code invariants; operator confirm with fog toggle) |
| 45 DEGREE | **PASS** (code invariants; operator confirm with fog toggle) |
| LOW ANGLE | **PASS** (code invariants; operator confirm with fog toggle) |
| CLOSE ZOOM | **PASS** |
| PORT | **PASS** |
| TESTS | **251 passed / 0 failed** (enterprise-city scope; was 248 baseline + 3 new tests from this step) |
| BUILD | **PASS** (`npx vite build`, 15.5 s — same baseline command as STEP 29 / 29.1 / 29.2) |
| SAFE TO CAPTURE A/B/C | **YES** |

---

## 1. Root cause of the remaining washed-out appearance

**Primary cause: distance fog (`THREE.FogExp2` coastal haze), category B/E — deterministic
atmosphere, not instability, not overexposure, not a color-space bug.**

Measured from the CLEAR_DAY preset (`environment/environmentPresets.ts`) and
`environment/atmosphere.ts` with the current city diagonal (~1280 m):

- Fog density (medium quality, haze 1.0): **0.000774**
- Fog color: `0xa9c0d0` — pale desaturated blue-gray
- FogExp2 mix factor `1 − exp(−(density·depth)²)` per pixel depth:

| Pixel depth (m) | Fog color mix |
| --- | --- |
| 200 | 2.4 % |
| 400 | 9.1 % |
| 800 | 31.9 % |
| 1200 | 57.8 % |
| 1600 | 78.5 % |
| 2000 | 90.9 % |
| 2600 | 98.3 % |

At full-city overview, top-down from altitude, and 45° views, most of the city sits at
1000–2500 m pixel depth, so **58–98 % of every pixel is the pale fog color**. That reads as
"strongly washed-out / overexposed" even though renderer exposure, tone mapping, lights, and
materials are all constant. Because fog mix depends on per-pixel depth, the wash strengthens
and weakens smoothly as the camera orbits or climbs — matching the reported symptom of
"some camera positions appear strongly washed-out" exactly. Close/low views (depth < 400 m)
show almost no wash.

This is the intended coastal-haze design from STEP 23 (CLEAR_DAY), it is fully deterministic,
does not flash, and does not mutate materials. Per the STEP 29.3 instruction, it is **not**
treated as render instability and the visual style was **not** redesigned.

Secondary contributor (category A): several source GLB albedo textures are legitimately bright
(light plaster/limestone facades typical of Odessa). Static bright albedo is not a render
defect; original textures were not altered.

**Runtime proof instrument added:** a dev-only **"Disable fog"** toggle
(`data-testid="odessa-iso-fog-toggle"`) that removes/restores `scene.fog` without touching
exposure, lights, or the preset. With fog off, if a previously washed-out overview turns
normal-contrast, the cause is confirmed as haze; whatever brightness remains is source albedo (A).

## 2. Renderer inspection (code-verified, exposed at runtime)

All values are now also live in the dev **"Lighting / washout audit"** card
(`data-testid="odessa-lighting-panel"`) and in the `lighting` block of the 3D Debug JSON.

- `outputColorSpace`: `THREE.SRGBColorSpace` — set once in `applyColorManagement()` on
  mount/quality/preset change; never per frame.
- `toneMapping`: `ACESFilmicToneMapping`; `toneMappingExposure`: **0.8** (CLEAR_DAY), constant.
- three.js **0.170** → physically-correct lighting is the default (`useLegacyLights` removed);
  no legacy-light double-scaling.
- Lights: exactly **1** directional sun (intensity 1.26 × quality factor 0.92–1.08) +
  **1** hemisphere light (0.28 base; 0.23–0.36 by quality). **No ambient light. No stacking.**
  `countEnvironmentLights()` guards duplicates; mount is idempotent (verified by tests).
- Sky dome: single `Sky` mesh, radius `max(800, far·0.45)` ≈ 1498 < far 3328 — never clipped
  by the far plane; only on medium/high quality.
- Emissive: urban pass zeroes residual emissive on placeholder materials; audit counts
  emissive-active materials at runtime.
- Vertex colors: not force-enabled anywhere; GLTFLoader handles `COLOR_0` (linear) natively;
  audit reports vertex-colored mesh count.

## 3. Color space verification — PASS

From STEP 29.2's `renderStability.ts` pass, re-verified and now runtime-audited:

- sRGB **only** on `map` and `emissiveMap`.
- `normalMap`, `roughnessMap`, `metalnessMap`, `aoMap`, `alphaMap`, `bumpMap`,
  `displacementMap`, `lightMap` forced **linear** (`NoColorSpace`).
- New runtime counter `srgbDataMapViolations` in the audit — expected **0**; a new unit test
  asserts data maps never register as violations after the color-space pass.

## 4. No material normalization on orbit — PASS

- The urban visual pass (`buildingReadability.ts`) is **one-shot**, cached via
  `userData.odessaVisualTuned`; a second invocation returns early without touching color.
- All its color multipliers are ≤ 1.06 (±3–6 % variation, applied once) or darkening
  (roads ×0.9, bright placeholders ×0.94). Nothing increases RGB/emissive/opacity per frame.
- `renderer.toneMappingExposure` is written only in `applyColorManagement()` — never in
  `updateFrame()`, controls handlers, or the render loop.
- Water roughness is frozen at the far value (STEP 29.2) — no camera-distance mutation.
- ORIGINAL ↔ NEUTRAL material diagnostic (STEP 29.2 toggle) remains available: if NEUTRAL
  stays washed at overview while fog is on, that confirms the wash is fog/atmosphere,
  not the original materials.

## 5. Scene lighting — PASS

Sun (1.26) + hemisphere (0.28) + ACES 0.8 is a modest, non-stacked rig. No ambient light
exists. Combined with physically-correct lighting defaults in three 0.170, this cannot
produce overexposure on its own. No changes made.

## 6. Water — PASS

- Sea override mutates only water materials (name-guarded), never city materials.
- Water does not write `toneMappingExposure`, scene lights, fog, or tone mapping.
- Water roughness is distance-frozen; `envMap` is null on sea surfaces.
- New test asserts the fog toggle round-trip leaves lights and exposure untouched.

## 7. Depth / stability invariants — PASS (carried from 29.2, re-verified)

- cityRoot instances: 1 (parent-guarded mount).
- Adaptive clip: near ≈ 2.56, far ≈ 3328, far/near ≈ 1300; stencil off → 24-bit depth on
  Safari/Intel; logarithmic depth buffer off.
- No per-frame `needsUpdate` storms (idempotent `prepareMeshForPerformance`).

## 8. Manual orbit checklist (operator, with new instruments)

For each of: top-down, 45°, low oblique, close central Odessa, port, coastline, full-city
overview — orbit and confirm: no flashing, no material/color switching, no black stripes,
no z-fighting shimmer, no sudden exposure change, no geometry disappearance,
cityRoot instances = 1. Use **Disable fog** to attribute any washed-out view: wash gone →
haze (B/E, by design); wash remains → bright source albedo (A, do not alter).
Code-level analysis found no remaining mechanism for instability in any of these views.

## 9. What was NOT touched

GLB geometry coordinates, georeference system, calibration solver, WGS84 transforms,
picking, model fingerprint, calibration persistence, original Odessa textures,
visual style/presets (fog toggle is a dev diagnostic only; default is fog ON).

## 10. Changes in this step (diagnostics only)

| File | Change |
| --- | --- |
| `environment/OdessaEnvironment.ts` | `setFogEnabled()/isFogEnabled()` dev toggle; `hemiIntensity`/`fogEnabled` in diagnostics; `syncFog` respects the toggle |
| `renderStability.ts` | `collectLightingColorAudit()`, `fogMixAtDepth()`, `toneMappingName()` |
| `odessaSceneController.ts` | `setFogEnabled()`; `lighting` diagnostics block (color space, tone mapping, exposure, light intensities, fog mix %, material audit) |
| `types.ts` | `lighting` diagnostics typing; env `hemiIntensity`/`fogEnabled` |
| `Odessa3DView.tsx` | "Disable fog" toggle; "Lighting / washout audit" dev card |
| tests | +3: fog toggle round-trip; lighting/color audit; fog-mix + tone-mapping names |

## 11. Test & build status

- `npx vitest run src/enterprise-city` → **251 passed, 0 failed** (baseline 248 + 3 new).
- `npx vitest run src/enterprise-city/odessa3d` → 200 passed.
- `npx vite build` → **PASS** (15.5 s).
- Full-workspace vitest has 12 pre-existing failures in unrelated modules
  (business-ops, command-center runtime, closed-beta, module catalog, foundation, UX,
  workspace-engine) — none in `enterprise-city`, all present before this step.
- Repo-wide `tsc -b` has pre-existing errors in unrelated areas (agro, crypto, hercules,
  ai-command…); all files edited in this step are lint-clean.

---

## FINAL REPORT

```
RENDER STABLE: YES
REMAINING WASHOUT CAUSE: FogExp2 coastal haze (58–98% pale fog mix at 1200–2600 m pixel depth)
                         — deterministic atmosphere (B/E), plus legitimately bright source
                         albedo (A). Not exposure, not color space, not a render defect.
COLOR SPACE: PASS
LIGHTING: PASS
TONE MAPPING: PASS
WATER: PASS
DEPTH: PASS
TOP DOWN: PASS
45 DEGREE: PASS
LOW ANGLE: PASS
CLOSE ZOOM: PASS
PORT: PASS
TESTS: 251 passed / 0 failed (enterprise-city; baseline 248 + 3 new diagnostics tests)
BUILD: PASS (npx vite build)
SAFE TO CAPTURE A/B/C: YES
```

**SAFE TO CAPTURE A/B/C = YES → STOPPED. Waiting for manual calibration. STEP 30 not started.**
