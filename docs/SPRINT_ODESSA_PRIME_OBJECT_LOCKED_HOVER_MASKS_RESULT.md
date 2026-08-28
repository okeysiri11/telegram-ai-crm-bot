# Sprint — Odessa Prime object-locked hover masks

**Date:** 2026-08-28  
**Branch:** `develop`  
**Sprint:** `ODESSA_PRIME_OBJECT_LOCKED_HOVER_MASKS`

Idle `/casino/lobby` shows only `hall.jpg`. Hover/focus lifts the photograph itself through SVG masks — no painted polygons, no floor fog, no ceiling rectangles.

## What shipped

- One base image + one photographic overlay (`<image href=hall.jpg>`), clipped by the active zone mask
- Mask paths stay inside `<mask>` (white fill, no stroke). Product mode never strokes or fills geometry
- Gold language is a masked warm wash + sign/lamp/pulse boost, not a polygon outline
- Slots: three cabinet masks + stools + 777 pulses. Floor reflection mask removed
- Bar: sign + bottle shelves + counter. Ceiling molding not in the mask
- Restaurant: sign + doorway + dining cluster + table lamps. No floating ceiling rectangle
- Debug outlines only at `?casinoHotspots=debug` in DEV
- Tooltip stays compact and zone-anchored. No mousemove React state

## Architectural decisions

- Visual highlight is a filtered copy of the same hall photograph, not a drawn overlay
- Hit `clip-path` polygons stay separate and invisible
- Coordinates remain normalized image percent (0–100) on the 1600×1066 fit box

## Intentionally deferred

Live viewport screenshot matrix (1366–2560) in a real browser. Vertex photography pass against `hall.jpg` if a mask still clips the wrong object.

## Next sprint

ODESSA PRIME CASINO — ROULETTE ROOM IMMERSION + PLAYABLE TABLE POLISH
