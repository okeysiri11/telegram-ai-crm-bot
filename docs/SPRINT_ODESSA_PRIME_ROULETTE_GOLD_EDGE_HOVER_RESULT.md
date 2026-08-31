# Sprint — Odessa Prime roulette gold-edge hover

**Date:** 2026-08-31  
**Branch:** `develop`  
**Status:** `PASS`  
**Commit:** not created (requested)

## What shipped

Roulette hover now uses the same method as slots: static open SVG paths in the 1600×1066 hall image box. Filled visual-polygon tints are not painted for roulette, so the floor and blackjack pit do not wash gold.

Hovering the sign, table, lamp, or chair activates one group: gold rims + tooltip + pointer. Click still opens `/casino/roulette/royale-1`.

## Architectural decisions

- Extend the hall overlay. New `RouletteGoldSvg` sits beside `SlotsPhotoOverlay`. No new `platform_*` package.
- Manual open paths only. No OpenCV, ImageMagick, or runtime image processing.
- Omit hidden or uncertain millimeters. A short real edge is preferred to a closed fake silhouette.
- Roulette and slots share gold-edge overlay mode (`usesGoldEdgeOverlay`) so neither zone paints filled polygons.

## Visual notes

| Part | Path |
|---|---|
| Sign | Four open sides around ROULETTE + MONTE-CARLO |
| Table | Wood-rail gold strip (felt boundary + ~12px) |
| Wheel | Front bowl-to-felt rim only |
| Lamp | Shade sides + stem on the lamp behind the wheel |
| Chair | Backrest top only (no footring; floor gold avoided) |

## Regression

- `hall.jpg` MD5 `6e44ad39a9a1b9898471a5b0e0117618`
- `hall-slots-gold-edge.png` MD5 `c48552d079822c76ec9e63c8d9bc4b7f`
- Slots hover and `/casino/slots` click unchanged
- Blackjack, poker, bar, restaurant zones untouched

## Build / test

- Vitest: 4 files, 19 tests, pass
- `npx vite build`: pass
- Browser 1440×900: idle / hover sign-table-chair-lamp / leave / click verified

Not committed, not pushed.
