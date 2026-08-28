# Sprint — Odessa Prime Casino facade polish + premium game cards

**Date:** 2026-08-28  
**Branch:** `develop`

Visual and performance polish of the existing `/casino` facade. No second casino, no real-money, no hall rebuild.

## What shipped

- Darker midnight facade, warmer gold bloom, photo-only hero (no duplicate SVG layer, no CSS `filter` on the photo)
- Removed empty debug geometry: door hitboxes, brass arch, columns
- Single header nav: ГОРОД · КАЗИНО · АКЦИИ · VIP · ТУРНИРЫ · ПОДДЕРЖКА
- Six premium game cards with local SVG assets + CSS hover (scale/border/glow, no React hover state)
- Parallax via CSS variables + rAF (no React mousemove state)
- Glass panels and header no longer use `backdrop-filter`
- Roulette / Blackjack / Slots / Poker (and remaining rooms) lazy-loaded behind `RoomSkeleton`

## Intentionally deferred

Interactive hall with spatial zones (next sprint). Image recompression of `facade.jpg` / `hall.jpg` (1600px, ~440–490KB) — quality kept.
