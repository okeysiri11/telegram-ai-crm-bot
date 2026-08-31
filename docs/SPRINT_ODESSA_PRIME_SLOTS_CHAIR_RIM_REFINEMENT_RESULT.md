# Sprint — Odessa Prime SLOTS chair gold rim refinement

**Date:** 2026-08-30  
**Branch:** `develop`  
**Status:** `COMPLETE`

## Locked machines

`hall-slots-gold-edge.png` MD5 before and after: `c48552d079822c76ec9e63c8d9bc4b7f`.  
Machine PNG, coordinates, opacity, timing, hit zone, tooltip, and `/casino/slots` were not changed.

## Method

Existing `SlotsChairSvg` only. Open paths, `fill="none"`.  
Two CSS layers from the same `d`: core `#f4ce7a` 1.75px, bloom 6px at 0.16 with 4px gold blur.  
Hover fade 220ms in / 180ms out. One-shot dash sweep 520ms.  
SVG uses `display: block` and `preserveAspectRatio="none"` so it fills the same box as the locked machine PNG.

Paths were aligned on `hall.jpg` at 1600×1066 (same space as the machine overlay), then checked on `/casino/lobby`.  
Chair 1 left side was omitted so the backrest is a rim, not a boxed U.  
Chair 3 seat was omitted after live hover showed it touching the cabinet. Chair 3 keeps a short visible backrest fragment only.

## Architectural decisions

- Extend `SlotsChairSvg`; do not rebuild the machine gold PNG.  
- Partial photographic rims are the success criterion.  
- Match machine overlay box mapping instead of `meet`, which can letterbox the strokes off the photo.
