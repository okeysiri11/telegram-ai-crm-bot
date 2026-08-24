# STEP 19 — Odessa 3D Performance + Smooth Navigation

## Shipped

- Demand-based render loop (`DemandRenderLoop`) — single RAF, stops when idle
- Event-driven rendering on camera/controls/load/resize/layer changes
- Adaptive pixel ratio (LOW/MEDIUM/HIGH caps + AUTO hysteresis controller)
- Quality presets expanded (antialiasing, shadows OFF, distances, anisotropy)
- Camera-priority tile streaming with heavy-chunk load/unload hysteresis
- Distance-based visibility for heavy assets (hide, not delete city tiles)
- Frustum culling + bounding volume compute on load
- Material performance pass (FrontSide, no shadows, capped anisotropy)
- OrbitControls tuning (damping, speeds)
- ResizeObserver with dimension dedupe
- Optional perf diagnostics panel under **Диагностика** (OFF by default)
- 9 new unit tests in `odessaPerformance.test.ts`

## Test / build

- `npm test -- src/enterprise-city` — **72 passed**
- `npx vite build` — **PASS**

## Architectural decisions

- **Non-heavy tiles retained once loaded** (STEP 18 invariant); only `heavy` layer uses unload hysteresis
- **Visibility toggling** separate from unload — distant heavy geometry hidden before unload threshold
- **AUTO DPR** uses stepped degradation (1.5 → 1.25 → 1.0) with 3s/8s hysteresis timers — avoids oscillation

## Deferred

- Web Workers for parse (not justified yet)
- Continuous render mode for future animated dynamic layers (flag scaffolded)

## Manual verification

Dev server: http://localhost:5181/enterprise-city → 3D Одесса → Debug → Диагностика
