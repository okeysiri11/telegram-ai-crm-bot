# Sprint — Odessa Prime slots: remove fake chairs

**Date:** 2026-08-30  
**Branch:** `develop`  
**Status:** `BLOCKED`

## Locked

`hall-slots-gold-edge.png` MD5 before and after: `c48552d079822c76ec9e63c8d9bc4b7f`.

## Removed

- `hall-slots-chairs-photo-edge.png`
- `build_hall_slots_chairs_photo_edge.py`
- ellipse/arc chair PNG overlay

SLOTS hover now paints only the locked machine gold edge. Tooltip, pointer, and `/casino/slots` are unchanged.

## SVG attempt (stopped)

Three open-path SVG groups were tried against `hall.jpg` (max 3 visual passes).  
Chair 3 strokes sat on the right machine cabinet, not the photographed stool.  
Those paths were deleted so they cannot paint over the accepted machine highlight.

## Why not PASS

Visible chair rims could not be aligned exactly in three short passes.  
No chair graphics ship. Machine hover is preserved.
