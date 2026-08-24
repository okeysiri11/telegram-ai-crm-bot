# STEP 23 — Odessa 3D visual environment + atmosphere baseline

## Shipped

- Dedicated `odessa3d/environment/` system, independent of GLB streaming
- Lightweight Preetham **Sky** (MEDIUM/HIGH) or solid maritime background (LOW)
- One `DirectionalLight` sun matched to sky sun position
- Hemisphere ambient (cool sky / warm ground bounce); fill light removed
- ACES tone mapping kept; exposure **0.86** (was 1.05) to reduce washed whites
- `FogExp2` coastal haze scaled from city diagonal — nearby geometry stays clear
- Canonical **WEB_water** Black Sea tint + distance roughness; STEP 20 duplicate/metalness guards kept
- Safe untextured white-building roughness/metalness correction; textured and colored mats untouched
- Presets: **CLEAR_DAY** implemented; SOFT_DAY / SUNSET / NIGHT are config stubs
- Quality: LOW no sky shader; MEDIUM/HIGH procedural sky; HIGH local shadows exist as a hook, **disabled**
- Diagnostics ENVIRONMENT section (preset, sun, fog, exposure, water mode, sky, quality)
- STEP 21/22 runtime (IDLE / INTERACTING / SETTLING, progressive activation, FPS guard) unchanged

Not modified: original GLBs, manifest IDs, geoTransform, 2D map, camera architecture. No WebGPU, SSAO, SSR, bloom, volumetrics, or full-city shadows. STEP 24 was not started.

## Visual system architecture

```
Scene
├── odessaEnvironment          ← sky + hemi + sun (created once)
│   ├── odessaSky              (MEDIUM/HIGH)
│   ├── odessaHemi
│   └── odessaSun
├── odessaCityRoot             ← GLB layers (streaming / activation)
└── scene.fog = FogExp2
```

Environment does not attach GLBs, does not traverse per frame, and does not rebuild on camera interaction. `updateFrame` only lerps cached WEB_water roughness.

## Sky

Three.js `Sky` (Preetham). CLEAR_DAY:

| | |
|---|---|
| turbidity | 3.1 |
| rayleigh | 1.55 |
| mieCoefficient | 0.0042 |
| mieDirectionalG | 0.74 |

Scaled to `camera.far * 0.45` so the dome stays inside the clip volume. LOW uses `scene.background` only.

## Sun

Elevation **42°**, azimuth **158°** (southeast/south visual range, not an ephemeris). Direction feeds both the Sky `sunPosition` uniform and the single directional light. Intensity 1.08, color `0xfff2dc`.

## Fog / haze

`FogExp2` color `0xc5d5e4`. Density from city diagonal so ~50% mix is near 0.84× diagonal (MEDIUM). At 80 m, mix &lt; 2%. Maritime `haze` 1.08.

## Water

STEP 20 still hides WEB_bay, keeps rivers, metalness 0, no envMap.

WEB_water only: color `0x1c5f6d` (Black Sea blue-green). Roughness ~0.60 near → ~0.80 far. No chrome, no SSR. LOW uses a constant far roughness (no distance updates).

## Material corrections

Untextured surfaces with luminance ≥ 0.88 and roughness &lt; 0.42 get roughness 0.50 and metalness ≤ 0.06. Authored color kept. Maps / water / colored buildings skipped.

## Quality-profile behavior

| Profile | Sky | Fog | Water | Shadows |
|---|---|---|---|---|
| LOW | background color | FogExp2 | sea tint, no distance lerp | off |
| MEDIUM / AUTO (desktop) | Preetham | FogExp2 | sea + distance roughness | off |
| HIGH | Preetham | slightly longer haze | richer near roughness | local hook, default **off** |
| AUTO (low-power) | same as LOW | | | off |

FPS guard thresholds from STEP 21 are unchanged.

## Performance (STEP 22 vs STEP 23)

Live Safari FPS was not captured in this session. Expected vs STEP 22:

| | STEP 22 | STEP 23 |
|---|---|---|
| City GLB count | 45 | **45** (unchanged) |
| City triangle count | authored GLBs | **unchanged** |
| Extra draw calls | 0 | **+1** sky box on MEDIUM/HIGH; **+0** on LOW |
| Extra lights | hemi + sun + fill | hemi + sun (**fill removed**) |
| Fog | none | FogExp2 (no extra draw) |
| Postprocessing | none | **none** |
| enterprise-city chunk | 693 kB | 708 kB (Sky shader) |

Interaction path does not recreate sky, lights, or water materials.

## Tests

`npm test -- src/enterprise-city` → **125 passed** (11 files).

New: create-once, dispose, quality switch without duplicates, LOW no sky, WEB_water-only sea override, preset validation, 2D/3D remount, untextured readability, nearby fog mix.

## Build

`npx vite build` → **PASS**.

## Remaining visual limitations

- No contact shadows / global shadow maps (intentional)
- Sky is analytic Preetham, not photographed HDRI
- Water is a tinted `MeshStandardMaterial`, not waves or SSR
- SOFT_DAY / SUNSET / NIGHT are stubs; no night city lights
- No weather API
- Building materials still come from Blender; only washed untextured whites are nudged
- Fog is distance-only, not height fog over the sea

## Manual checklist (for Safari / Intel Mac)

A–J as specified: overview, coastline, port, center, close buildings, low-angle horizon, rotate over sea, zoom, close pan, 2D↔3D remount. Expect no brown streaks, no flashing sea, no duplicate sky/lights, far fade, more building depth, responsive camera.

## Files changed

New:

- `src/web/src/enterprise-city/odessa3d/environment/OdessaEnvironment.ts`
- `environmentPresets.ts`
- `sunController.ts`
- `atmosphere.ts`
- `waterEnvironment.ts`
- `buildingReadability.ts`
- `index.ts`
- `environment.test.ts`
- `docs/STEP_23_ODESSA_3D_ENVIRONMENT_RESULT.md`

Modified:

- `odessaSceneController.ts`
- `Odessa3DView.tsx`
- `scenePrep.ts`
- `qualityProfile.ts`
- `types.ts`
- `index.ts`
- `odessaPerformance.test.ts`
