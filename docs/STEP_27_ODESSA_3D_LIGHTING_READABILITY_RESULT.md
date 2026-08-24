# STEP 27 — Odessa 3D lighting depth + material balance

## Status

Shipped a cached daylight / readability pass on the STEP 23 environment. STEP 21–26 performance, LOD, streaming, water guard, and original GLBs are unchanged. No SSAO, no global shadow maps, no composer. STEP 28 was **not** started.

## Lighting before (CLEAR_DAY)

| Knob | Value |
|---|---|
| Sun | DirectionalLight `#fff2dc` intensity **1.08**, elevation **42°**, azimuth **158°**, no shadow map |
| Fill | HemisphereLight sky `#c4d6ea` ground `#8b7d6a` intensity **0.36** |
| Extra fills | none |
| Sky | THREE.Sky on MEDIUM/HIGH, off on LOW |
| Tone map | ACES Filmic, exposure **0.86**, `SRGBColorSpace` |
| Fog | FogExp2 `#c5d5e4` (pale, near-white) × haze 1.08 |
| Untextured mats | only lum ≥ 0.88 got roughness 0.58 / metalness 0.06 |
| Water | `#1c5f6d`, metalness 0, roughness 0.6–0.8, no envMap |

That fill + pale fog + near-vertical-enough sun is why blocks read as CAD-flat.

## After

- Sun **34° / 148°**, intensity **1.26** (HIGH ×1.08, LOW ×0.92). Hemi fill **0.28** (HIGH ×0.82). One sun + one hemi only.
- Exposure **0.80** ACES. Stronger sun, slightly lower exposure → facade relief without roof clip.
- Fog `#a9c0d0` coastal blue-gray, haze 1.0, still city-scale FogExp2. Not a white wall.
- Water `#154e5a` (darker than sky), roughness 0.62–0.82, metalness 0, no envMap, WEB_water only.
- Untextured placeholder urban materials classified once at parse-prep: BUILDING / ROAD / GROUND / VEGETATION / WATER / INDUSTRIAL / UNKNOWN.
- BUILDING: metalness 0, roughness 0.55–0.85, slight white crush, deterministic ±3–6% brightness from `hash(assetId + materialName)`.
- ROAD: slightly darker, rough, no spec. Textured materials never touched.
- HIGH only: one-time downward-normal sample as a cheap base darken. Not SSAO.
- LOW: sun+hemi+background, classify only, no variation.

All of this is userData-cached. Camera motion does not rebuild lights or reclassify.

STEP 28: **NO**.
