# STEP 25.2 — Odessa 3D runtime recovery

## Result

`/enterprise-city` → **3D Одесса** must paint a canvas + HUD instead of the route boundary `"This view failed to render"`. STEP 26 was **not** started. Original GLBs were not modified.

## Root cause (runtime, not tests)

Two cooperating defects after STEP 25 / 25.1:

1. **`Odessa3DView` unmounted the canvas when `initError` was set** (`Odessa3DView.tsx`, former early `return` around the old line 138). React StrictMode (`src/web/src/main.tsx`) double-mounts: controller A can still finish `await loadOdessaManifest()` and create a WebGL context after cleanup, then controller B fails on the same canvas. Safari then set `initError`, the canvas disappeared, and a retry could not recover.

2. **HUD render was not normalized.** STEP 25.1 bound `const total = progress.total`, but first paint still read loader fields with no single safe object. A missing/partial `progress` (pre-manifest `total`, HMR, or a second ReferenceError) still escaped to `RouteErrorBoundary` (`App.tsx` zone `"Enterprise City"`).

## Fix

- One `normalizeHudProgress()` object for HUD (`hud.total` is `0` until the loader/manifest count exists, then `45`). No free `total` in the view render scope.
- Canvas always stays mounted. Init failure overlays a **temporary local diagnostic panel** (phase, error name/message/stack, manifest/controller/WebGL, progress JSON).
- `Odessa3DErrorBoundary` catches render throws inside 3D so the city route stays up.
- `OdessaSceneController.mount()` aborts after dispose; does not rethrow after `onInitError`; `initRenderer` requires w/h ≥ 1, runs once, and `dispose()` calls `forceContextLoss()`. Manifest register is followed by `emitHudProgress()` so `total` becomes the real asset count.

## Files

- `src/web/src/enterprise-city/odessa3d/Odessa3DView.tsx`
- `src/web/src/enterprise-city/odessa3d/odessaSceneController.ts`
- `src/web/src/enterprise-city/odessa3d/hudProgress.ts`
- `src/web/src/enterprise-city/odessa3d/Odessa3DErrorBoundary.tsx`
- `src/web/src/enterprise-city/odessa3d/Odessa3DView.test.tsx`
- `src/web/src/enterprise-city/odessa3d/hudProgress.test.ts`

STEP 26: **NO**.
