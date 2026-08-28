# Sprint — Odessa Prime Casino interactive hall + spatial zones

**Date:** 2026-08-28  
**Branch:** `develop`

Turn `/casino/lobby` into a spatial hall: the interior photograph is the interface. Facade is unchanged. No second casino, no real-money.

## What shipped

- Six invisible polygon zones mapped to visible objects in `hall.jpg` (1600×1066): Roulette Monte Carlo, Blackjack Salon, Poker Room, Restaurant, Bar, Slots
- Hover/focus illuminates the physical area (SVG fill/stroke), slightly dims the rest, shows a small gold label, and eases a 1.035 camera focus toward the zone
- Click brightens the zone, zooms to ~1.055, then navigates in 420ms (immediate when `prefers-reduced-motion`)
- Permanent translucent navigation rectangles removed; labels appear only while a zone is active
- Keyboard: Tab order Roulette → Blackjack → Poker → Restaurant → Bar → Slots; Enter/Space enters
- Touch: first tap focuses and shows the label; second tap enters
- Dev-only calibration: `?casinoHotspots=debug` in development
- Coordinates live in one config: `src/web/src/casino/lobby/hallZones.ts` (normalized 0–100 image space)
- Hall image is a single `<img>` filling an aspect-ratio stage (no CSS `cover` crop, no duplicate background)

## Architectural decisions

- Extend the existing lobby scene; do not add a new casino package or duplicate rooms
- Hit testing uses CSS `clip-path` polygons; visual glow is a pointer-events-none SVG overlay with the same polygons
- React state updates only when the active/entering zone id changes — no mousemove/pointermove handlers
- Hall click navigates after the local zoom; it does not stack `useRoomTransition().go()`’s extra 180ms delay
- Bar and restaurant keep the existing lightweight `AtmosphereRoom` destinations with `← В ЗАЛ`
- VIP remains on the schematic map / games list, not as a hall rectangle (it is not a distinct object in the photograph)

## Intentionally deferred

Roulette room immersion and a playable table (next sprint). Fine-tuning hotspot vertices against a live 2560×1440 viewport (dev calibration query is in place). Hall.jpg recompression.

## Verification

- Scoped vitest (hall + lobby + live + world + routes + entrance + facade + platform entry): pass
- Production client build: `npx vite build` in `src/web` — pass (`✓ built in 2m 15s`)
- `tsc -b` still reports pre-existing errors in unrelated city/agro/recruiting modules and older casino tests that import `node:fs`; this sprint’s hall test does not add that pattern
- Backend tests not run (no Python changes)
