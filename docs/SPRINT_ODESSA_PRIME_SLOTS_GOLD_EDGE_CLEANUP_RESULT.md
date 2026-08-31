# Sprint — Odessa Prime slots hover gold-edge cleanup

**Date:** 2026-08-29  
**Branch:** `develop`  
**Status:** `BLOCKED`

## Intent

Replace the photographic-foreground brightness wash with a build-time gold contour around the three real GOLD machines and three real chairs. Idle hall stays clean. Click still opens `/casino/slots`.

## What changed

- Hover paints `hall-slots-gold-edge.png` only (opacity 0 → 1, 180ms ease-out).
- Removed brightness / saturate / large drop-shadow wash from `.op-slots-photo`.
- `hall.jpg` and `hall-slots-foreground.png` were not rewritten.
- Hit polygons, routes, and other rooms were not changed.
- Edge PNG is generated at build time by `src/web/scripts/build_hall_slots_gold_edge.py` (no runtime segmentation).

## Architectural decisions

- Extend the existing slots overlay (`SlotRightHover` + `slotRightMask`) instead of a new hover module.
- Keep the photographic foreground PNG as DEV inspector source only.
- Derive machine crowns from the largest warm component in a tight crown ROI so bar-bottle gold is not seeded.
- Chair pixels come only from visible photo contrast; geometric `chair_mask()` drawings are not used.

## Browser check

Opened `/casino/lobby` on the Vite host. Idle hall is clean (no gold overlay). Focusing the SLOTS hotspot sets `data-slots-hovered=true`, overlay `opacity: 1`, `src=/assets/casino/lobby/hall-slots-gold-edge.png`, and the existing tooltip.

That is not enough. The live hover does not show a clean gold contour around all three real chairs. Machine crowns have a jagged gold trace plus internal 777/panel edges; chairs are fragments/blobs, not photographic silhouettes.

## Why not PASS

- Chair contours are incomplete (backrest fragments / seat blobs, not a readable outline of all three real chairs).
- Machine edges still include internal 777 / panel traces and stair-step aliasing.
- A hand cursor and tooltip already worked; they are not accepted as the visual result.

Until `CHAIR_1/2/3_GOLD_EDGE` can be honestly YES against the photograph, this sprint stays `BLOCKED`.
