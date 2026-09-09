# Odessa Prime Casino — Phase 4.7 True physical slot control surface

**Date:** 2026-09-09

The seated cabinet is the interface. Hit zones are percentage-based on each PNG. Shared `slotEngine` / `useSlotDemo` are unchanged besides demo cashout and insert-bill credits.

## What shipped

- Transparent physical hit zones for SPIN, CASH OUT, SERVICE, INSERT CARD, INSERT BILL, and BET 50/100/250/500 aligned to painted deck keys.
- BET 10 / BET 25 / AUTO use the nearest unpainted deck plate (above 50/100, and left of SPIN). Documented on each control (`painted: false`).
- BAL/BET/WIN live inside the monitor glass. No floating SPIN/BET web bar. No fake armchair/ashtray overlay.
- Hover and press illumination follow the hit-zone shape (rect / round / slot). Keyboard focus + Russian `aria-label`s.
- Catalog steps: `[10, 25, 50, 100, 250, 500]`. Insert bill adds 500 demo credits. Cashout clears the playable balance.

## Architectural decisions

- New `cabinetControls.ts` owns per-machine geometry. `usePhysicalCabinetControls.ts` owns cashout/service/card/bill/auto. Rejected a second engine and WebGL.
- Hall `PhysicalSlotMachine` and `cabinetGeometry.generated.ts` stay as the hall contract.

## Tests / build

`vitest run src/casino/games/slots/slotsHall.test.tsx src/casino/games/slots/slotEngine.test.ts` — pass.
`npx vite build` — pass.

## Visual (1920×1080 Chromium)

See `artifacts/casino/phase47-*.png`. No vertical scroll. Hover SPIN glow. BET 25 updates in-glass СТАВКА.
