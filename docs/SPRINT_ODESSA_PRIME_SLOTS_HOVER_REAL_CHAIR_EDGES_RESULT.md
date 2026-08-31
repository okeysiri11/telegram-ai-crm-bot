# Sprint — Odessa Prime SLOTS hover: real chair edges only

**Date:** 2026-08-30  
**Branch:** `develop`  
**Status:** `BLOCKED`

## Locked machines

`hall-slots-gold-edge.png` MD5 before and after: `c48552d079822c76ec9e63c8d9bc4b7f`.  
Machine PNG, mask, hit polygons, tooltip, and `/casino/slots` were not changed.

## Fake chair layer

Removed earlier this session: chair PNG overlays, ellipse/circle/closed-silhouette builders.  
SLOTS hover no longer paints synthetic stools.

## SVG method

`SlotsChairSvg` — three independent groups in the 1600×1066 hall space.  
Idle opacity 0; SLOTS hover opacity 1; 180ms ease-out; same existing hit zone.  
All path arrays are empty after the third live hover check.

## Three visual passes

1. Grid-traced open paths — chair 3 sat on machine 3.  
2. Left-shift — chairs 1–2 closer; chair 3 still on the cabinet.  
3. Chip-corrected rims, then live `/casino/lobby` hover — chairs 1–2 floated left of the photo stools; chair 3 had no safe stroke.

Per the sprint stop rule every chair path was deleted. No fourth pass.

## Why not PASS

Browser hover showed gold arcs that were not on the photographed chair rims.  
Chair 1 sat left of its stool. Chair 2 sat in the gap. Chair 3 cannot be separated from the right GOLD cabinet.

## Architectural decisions

- Extend `SlotsPhotoOverlay` with an SVG sibling; do not regenerate `hall-slots-gold-edge.png`.  
- Rejected another raster/contrast extraction pass (forbidden by the sprint).  
- Empty chair groups stay in the contract so a later photo-exact trace can fill them without a new hit zone.
