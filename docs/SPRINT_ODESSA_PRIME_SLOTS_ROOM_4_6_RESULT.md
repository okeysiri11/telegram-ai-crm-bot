# Odessa Prime Casino — Phase 4.6 First-person seated slot experience

**Date:** 2026-09-08

Close first-person sit-down play over the accepted Phase 4.4A hall and Phase 4.5 seated route. Shared demo engine, six cabinet PNGs, and hall catalog are unchanged.

## What shipped

- `/casino/slots/:machineId` now uses a close seated crop (`--seated-h` ≥ 150%) so the selected cabinet dominates a 1920×1080 viewport instead of the Phase 4.5 distant `84%` / `28rem` silhouette.
- Foreground armchair armrests + a side-table ashtray cue the seated POV. The hall chair is not placed between the player and the machine.
- Gameplay chrome lives on the cabinet: BET 10/25/50/100, SPIN, AUTO, HISTORY, BAL/BET/WIN. HUD outside the machine is only «Назад к автоматам» and «Демо-режим» plus the global casino shell.
- Reel overlay is inset per cabinet and clipped (`overflow: hidden`, `contain: paint`, `clip-path`) so live reels stay inside the monitor glass.
- Hall → machine approach stays ~720ms (140ms if `prefers-reduced-motion`); seated view eases in ~640ms and reverses on back.
- Background is darker, mildly blurred, vignetted, with light bokeh and local cabinet glow. The cabinet itself is not blurred.
- One seated renderer only (selected cabinet). CSS transforms, PNG, SVG/DOM overlays. No extra WebGL.

## Architectural decisions

- Presentation-only seated view. Rejected a second engine, a WebGL cabinet, and a detached web control card.
- Keep `/casino/slots/:machineId` so existing tests, history, and Odessa Gold stay valid.
- Per-machine crop/inset in `cabinetPlayGeometry.ts` rather than regenerating hall `cabinetGeometry.generated.ts`.
- Hall `is-choosing` scale bumped to 1.36 so the camera approach continues into the seated crop.

## Tests

Targeted `vitest run src/casino/games/slots/slotsHall.test.tsx src/casino/games/slots/slotEngine.test.ts` — pass.

Coverage includes seated composition for all six machines, identity, BET 10/25/50/100, SPIN lock, AUTO, HISTORY on the cabinet, screen containment math/CSS, back to hall, no `28rem` distant cabinet, no detached web panel.

## Build

`npx vite build` in `src/web` — pass.

## Visual acceptance (1920×1080 Chromium)

Against the local Vite dev server. Scroll delta 0. Reel `getBoundingClientRect` contained in the screen overlay for all six machines. Interactive BET/SPIN/AUTO/HISTORY verified on Olympus Crown.

Screenshots:

- `artifacts/casino/phase46-hall.png`
- `artifacts/casino/phase46-olympus-seated.png`
- `artifacts/casino/phase46-olympus-spin.png`
- `artifacts/casino/phase46-candy-fortune-seated.png`
- `artifacts/casino/phase46-pharaohs-book-seated.png`
- `artifacts/casino/phase46-big-catch-seated.png`
- `artifacts/casino/phase46-buffalo-fortune-seated.png`
- `artifacts/casino/phase46-lady-emerald-seated.png`
- `artifacts/casino/phase46-emerald-1440.png`
- `artifacts/casino/phase46-pharaohs-1366.png`

## Intentionally deferred

- Replacing baked PNG bet labels (50/100/250/500) with 10/25/50/100 art. Interactive overlays already use catalog steps.
- Photoreal 3D perspective warp of the reel plane (would require WebGL).
