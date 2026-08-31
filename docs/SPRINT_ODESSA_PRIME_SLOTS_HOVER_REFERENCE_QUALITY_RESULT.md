# Sprint — Odessa Prime SLOTS hover, reference-quality chair rims

**Date:** 2026-08-30  
**Branch:** `develop`  
**Status:** `NEEDS_MANUAL_REFINEMENT`  
**Commit:** not created (requested)

## What shipped

Chair hover visuals were rebuilt as static open SVG paths in the same 1600×1066 space as `hall.jpg`.

- Machine gold PNG, hit zone, tooltip, and `/casino/slots` were not changed.
- Failed aisle-left / ellipse / closed-shape chair strokes were removed.
- Remaining strokes are short open paths on photographed warmth only.
- Chair 3 has no path: every candidate sat on the machine “GOLD/DOLLAR” plate.

## Architectural decisions

- Extend `SlotsChairSvg` only. Do not regenerate `hall-slots-gold-edge.png`.
- Trace visible photo edges by hand. No OpenCV, thresholding, or ellipse generation.
- If an edge is not confident, omit it. A missing segment is acceptable; a fake segment is not.
- SVG `viewBox="0 0 1600 1066"` and `preserveAspectRatio="xMidYMid meet"` so the overlay tracks `hall.jpg` (`object-fit: contain`) inside the 1600/1066 hall wrap.
- Chairs stay visual children of the existing SLOTS hover flag. No new hit zones.

Rejected: shifting chairs into the left aisle (x ~1180–1250). Pixel samples there are marble veins, not stools. Stools sit in front of the three GOLD cabinets.

## Locked assets

| File | MD5 |
|---|---|
| `hall.jpg` | `6e44ad39a9a1b9898471a5b0e0117618` |
| `hall-slots-gold-edge.png` | `c48552d079822c76ec9e63c8d9bc4b7f` |

## Visual gate (3 manual passes)

Pass 1–2 aisle-left arcs sat above backrests and on empty floor. Removed.

Pass 3 kept only:

- Chair 1 seat glint (~1282–1292, y 734)
- Chair 1 foot-ring glint (~1290–1306, y 822)
- Chair 2 seat-edge warmth under machine 2 (~1400–1424, y 756)

Chair 3 omitted after the path landed on the cabinet plate.

This is not the supplied reference (thin gold on all three full silhouettes). Machines still dominate; chairs are partial.

## Regression

| Check | Result |
|---|---|
| SLOTS hover | yes |
| Tooltip | yes |
| Click `/casino/slots` | yes |
| Machine visual | unchanged |
| hall.jpg | unchanged |
| 1440 / 1600 / 1366 | hover + chairs share one state |

## Build / test

- `npx vitest run --maxWorkers=1` hall/chair files: 3 files, 17 tests, pass
- `npx vite build`: see sprint close-out
- Not committed, not pushed
