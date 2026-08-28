# Sprint — Odessa Prime hall object zones + full-width stage

**Date:** 2026-08-28  
**Branch:** `develop`

Recalibrate `/casino/lobby` spatial navigation: object-based multi-polygons, full-width undistorted hall image, overlay locked to the image box, compact tooltip anchors.

## What shipped

- Hall stage is `width: 100%` with `aspect-ratio: 1600 / 1066`; image uses `object-fit: contain` inside that box (no stretch)
- Ultrawide lobby cancels `--op-uw-pad` so the photograph spans the main column
- Overlay is a sibling of the image inside `hall-image-wrap` (`inset: 0`)
- Six logical destinations remain; roulette and slots are multi-polygon object sets; crude single quads removed
- One tooltip per logical zone, anchored beside the object and clamped inside the stage
- Hover state lives in `HallSpatialOverlay` only; camera scale is CSS variables on the focus layer (no mousemove React state)
- Click focus is 240ms, skipped under `prefers-reduced-motion`

## Architectural decisions

- Split `LobbyHall` (static image stage) from `HallSpatialOverlay` (active zone + tooltip) so lobby chrome does not rerender on hover
- Keep coordinates in `hallZones.ts` only
- Do not use canvas / WebGL / pixel masks

## Intentionally deferred

Live visual QA at 1366 / 1920 / 2560 / 3440 (no browser screenshot tooling in this session). Vertex fine-tuning against a photographed pass. Next: Roulette Monte-Carlo immersive room.
