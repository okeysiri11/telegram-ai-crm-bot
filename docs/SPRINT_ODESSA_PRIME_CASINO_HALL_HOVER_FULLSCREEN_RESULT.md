# Sprint — Odessa Prime premium hall hover + fullscreen fit

**Date:** 2026-08-28  
**Branch:** `develop`

Make `/casino/lobby` fill the desktop viewport without scrolling, and replace milky polygon fills with object-traced gold glow.

## What shipped

- Desktop lobby fills `100dvh` below the casino header; hall uses a contained aspect-ratio box (`1600/1066`) centered in the remaining space
- Hit polygons stay invisible; visual layer uses gold stroke + light fill (`~5.5%`) and a tiny SVG glow filter only while a zone is active
- Hover camera is `1.012` (click `1.015`); click-to-route is 200ms
- Tooltips stay destination-anchored; poker secondary line is `ODESSA PRIME`; blackjack heading is `BLACKJACK`
- Overlay hover state remains isolated from lobby chrome; no mousemove React state

## Intentionally deferred

Live visual QA at 1280–2560 in a real browser (no screenshot tooling here). Vertex photography pass.
