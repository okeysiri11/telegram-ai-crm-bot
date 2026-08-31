# Sprint — Odessa Prime slots foreground PNG

**Date:** 2026-08-29  
**Branch:** `develop`  
**Status:** `BLOCKED` — PNG exists, browser silhouette acceptance not met

## Source

`src/web/public/assets/casino/lobby/hall.jpg` — 1600×1066

## Foreground

`src/web/public/assets/casino/lobby/hall-slots-foreground.png` — 1600×1066 RGBA  
Builder: `src/web/scripts/build_hall_slots_foreground.py`

Numeric: has alpha, ~97% transparent, opaque bbox ≈ (1267, 485, 1600, 882).

## Why not PASS

Automatic seed/dilate + geometric chairs do not yet follow photographic silhouettes tightly enough (crown curves, chair 2/3 bodies, gap bleed). Playwright Chromium cannot launch on this host, so live `?casinoMaskDebug=slots` inspection was not completed in a real browser.

## Wired (ready after mask fix)

- Hover uses the PNG at opacity 0/1 with brightness 1.20, saturate 1.25, gold drop-shadow from alpha.
- DEV inspector: `/casino/lobby?casinoMaskDebug=slots`
- Existing SLOTS pointer / tooltip / click unchanged.
