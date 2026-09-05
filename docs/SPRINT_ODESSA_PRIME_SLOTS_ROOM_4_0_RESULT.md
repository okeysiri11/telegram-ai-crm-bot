# Odessa Prime Casino — Phase 4.0 Slots Room

**Date:** 2026-09-05  
**Mode:** Hall rebuild + shared demo engine. No real-money gambling. No provider integration.

## Root cause

`SlotParlor` was a vertically stacked room: cinematic backdrop (`min-height: 52vh`), three
dashboard-like cabinets (one live Odessa Gold, two “автомат позже” teal screens), and
`RoomNavigation` “ДАЛЕЕ · ПОКЕР” below the fold. Game selection and the only playable
machine lived on different pages. Guests hitting PLAY on Odessa Gold were sent to auth.

## What shipped

- Full-viewport `SlotsHall` (`/casino/slots`) with six distinct themed cabinets
- Provider-ready `SLOT_CATALOG` + search/filters
- Shared `slotEngine` / `useSlotDemo` (result → state → animation)
- Cabinet focus view at `/casino/slots/:machineId`
- Existing `/casino/slots/odessa-gold` server PLAY path preserved
- Hall → machine → hall → lobby stays inside `CasinoShell`

## Tests

- `src/web/src/casino/games/slots/slotEngine.test.ts`
- `src/web/src/casino/games/slots/slotsHall.test.tsx`

## Architectural decisions

- Demo play for the six new machines is client-authoritative with a labelled **Демо-режим**
  wallet. Odessa Gold keeps the existing server spin contract.
- Cabinets are CSS/DOM, not six WebGL canvases. Game screen is lazy-loaded.
- Catalog fields include `providerId`, `externalGameId`, `demoAvailable`, `realAvailable`
  so a future provider does not force a UI rewrite.
