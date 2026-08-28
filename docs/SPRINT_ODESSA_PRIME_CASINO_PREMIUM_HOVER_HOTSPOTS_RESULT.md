# Sprint — Odessa Prime premium hover hotspots + clean immersive hall

**Date:** 2026-08-28  
**Branch:** `develop`  
**Sprint:** `ODESSA_PRIME_CASINO_PREMIUM_HOVER_HOTSPOTS`

Idle `/casino/lobby` shows only the hall photograph. Gold object traces, pulses, and tooltips appear for one active zone on hover, keyboard focus, or touch, then clear on leave.

## What shipped

- Hit geometry stays invisible (`clip-path` spans). Visual glow is a separate SVG stroke layer.
- Idle visual polygons: `fill="none"`, `stroke="none"`, opacity 0, no filter.
- Hover/focus: champagne-gold rim glow, sign/lamp/pulse roles, one-shot light trace (~520ms), then static glow until leave.
- Slots use three cabinet rims + 777 pulses + a thin floor reflection, not a single rectangle fill.
- Compact glass tooltip (opacity + scale, 160ms), one tooltip at a time. Bar/restaurant secondary line is `ODESSA PRIME`.
- Full-image dim overlay removed. No mousemove React state. Viewport-fit hall from the previous sprint is preserved.

## Architectural decisions

- Keep coordinates in `hallZones.ts`. Extend `visuals` to `{ polygon, role }` so hit polygons can stay generous while paint follows objects.
- Do not introduce canvas/WebGL/pixel masks.
- Debug outlines remain behind `?casinoHotspots=debug` in development only.

## Intentionally deferred

Live visual QA at 1366 / 1440 / 1600 / 1920 / 2560 in a real browser (no screenshot tooling in this session). Vertex photography pass against `hall.jpg`.

## Tests / build

- `npx vitest run src/casino/casinoHallSpatial.test.tsx src/casino/casinoLobby.test.tsx src/casino/casinoLive.test.tsx src/casino/casinoRoutes.test.tsx src/casino/casinoWorld.test.tsx`
- `npx vite build`

## Next sprint

ODESSA PRIME CASINO — ROULETTE ROOM IMMERSION + PLAYABLE TABLE POLISH
