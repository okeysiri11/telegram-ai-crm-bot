# STEP 26 — Odessa 3D image stability + anti-shimmer

## Status

Shipped a conservative quality pass on the existing STEP 21–25 runtime. Progressive fetch/parse/activation, virtual LOD, streaming pause, water guard, and original GLBs are unchanged. STEP 27 was **not** started.

## Measured render path (before)

| Knob | Actual value |
|---|---|
| AUTO antialias | **forced false** (`qualityProfile.ts` AUTO override) |
| MEDIUM / HIGH antialias | true |
| LOW antialias | false |
| AUTO pixelRatioCap | 1.25 desktop / 1.0 low-power, **start step 1.0** |
| MEDIUM pixelRatioCap | **1.0** |
| HIGH pixelRatioCap | 1.5 |
| Interaction DPR | immediate −0.25 while INTERACTING |
| Adaptive floor | **0.75** after ~3.5s of FPS < 27 |
| Tone mapping | ACES Filmic, exposure 0.86, `SRGBColorSpace` |
| Texture anisotropy | `Math.min(tex.anisotropy \|\| 1, cap)` → **stayed 1** |
| minFilter / mipmaps | not set |
| LOD hysteresis | 0.18 |
| Logarithmic depth | **false** (kept) |
| Camera near | clamped 0.5–2.0 from city diagonal |

## Root cause of shimmer

Primary: **geometry aliasing + undersampling**, not missing meshes.

4-core Intel laptops were classified as low-power (`hardwareConcurrency <= 4`), which forced AUTO `antialias: false` and the LOW streaming preset on the user's Safari machine. Threshold is now `<= 2` plus mobile viewport.
2. MEDIUM capped DPR at 1.0; AUTO started at 1.0; orbit immediately dropped another 0.25 → visible DPR pumping.
3. Textured materials never received mipmaps / raised anisotropy (code only capped the default 1).

LOD popping is not the city-tile path (city/sea stay visible). Heavy-tile hysteresis 0.18 was tightened anyway. No building z-fighting pair was found; logarithmic depth stays off; polygonOffset remains water-only.

## After

- AUTO desktop / MEDIUM / HIGH: native MSAA `antialias: true` at **init only**. LOW stays false.
- DPR: LOW 0.85–1.0, MEDIUM/AUTO 1.0–1.25, HIGH 1.25–1.5, never above `min(devicePixelRatio, 1.5)`.
- No immediate DPR dip on orbit. Step down only after FPS < 26 for 3s. Step up only when idle (8s healthy, or idle-boost after 650 ms).
- Textures: `LinearMipmapLinearFilter` + `LinearFilter` + anisotropy LOW 1 / MEDIUM 4 / HIGH 8 (GPU-clamped). Untextured materials untouched.
- LOD hysteresis 0.18 → 0.28. Coast/sea protection unchanged.
- Untextured washed-white buildings: roughness floor 0.58 (color unchanged).
- HUD QUALITY block: mode, pixelRatio, antialias, anisotropy, FPS, interactionState, visible/hidden assets, LOD transitions/sec, triangles, drawCalls.

## Known limits

Native MSAA is 4x at best on this path — no FXAA/TAA composer. A single huge GLB parse can still hitch (STEP 25). Intel Safari remains fill-rate limited; AUTO may sit at DPR 1.0 after a long poor-FPS orbit until idle restore.

STEP 27: **NO**.
