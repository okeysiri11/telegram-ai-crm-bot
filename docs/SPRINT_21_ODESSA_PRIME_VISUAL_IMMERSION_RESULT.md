# Sprint 21 — Odessa Prime visual immersion

Play-money only. Extends Sprint 20. No real-money, no payments, no `/api/v1` or `/management/v1` changes. No authentication or route-table changes.

## Architectural decisions

- **Extend `src/web/src/casino/` presentation.** Tokens on `.op-root` are the art bible (marble, wood, brass, felt, burgundy, lamp gold, fog). Rooms and tables consume them. No new `platform_*` package, no Three.js / `odessa3d`.
- **Shared room-transition provider in `CasinoShell`.** `useRoomTransition().go()` from lobby hotspots, map, and `RoomNavigation` drives the same veil the shell renders. React Router is unchanged. Timings stay 180 ms leave / 520 ms enter. `data-testid="room-transition"` kept.
- **Live tables are CSS/DOM chrome only.** Roulette pit + lamp + wood rail; blackjack lamp + brass rail. `casinoApi`, wheel math, bet lock, and СДАТЬ / ЕЩЁ / ХВАТИТ / УДВОИТЬ are untouched.
- **Rejected:** Framer Motion / nested `RoomStage` (would double-mount the veil); new `immersion.css` package file (composition already exists: `odessa` → `world` → `rooms-visual` → `live` → `ambient`); auth/guest/catch-all reopening.

## What shipped

- Unified Odessa Prime palette: near-black / graphite / navy, black marble, dark wood, brushed brass, green felt, burgundy accents, warm chandelier pools, soft fog.
- Cinematic entrance: brass arch, marble sheen, burgundy runner, lamp pool, fog.
- Lobby and atmosphere rooms share the same lighting language (chandelier + lamp pool + fog).
- Threshold veil: marble wash + brass rim + gold ambient pool (door-threshold, not a wipe).
- Live roulette presented as a seated pit; live blackjack as a lit felt salon.
- Extra glow/fog gated by existing `[data-tier="LOW"]` and `prefers-reduced-motion`.

## Routes

Unchanged from Sprint 20. Catch-all stays `CasinoUnknown` inside the casino. `/casino/roulette/table/royale-1` and `/casino/roulette/royale-1` remain the live table.

## Test / build

- `npx vitest run src/casino/casinoImmersion.test.tsx src/casino/casinoLive.test.tsx src/casino/casinoWorld.test.tsx src/casino/casinoRoutes.test.tsx` — **25 passed**
- `.venv/bin/python -m pytest tests/test_casino_world.py tests/test_casino_premium.py tests/test_casino_immersive.py tests/test_casino_foundation.py -q` — **29 passed**
- `npx vite build` — **success** (`casino-*.css` 34.9 kB, `casino-*.js` 43.9 kB)
- `npx tsc -b --pretty false` — **CASINO_NEW_ERRORS=0**; pre-existing `tsc` debt remains outside casino (ai-command, odessa3d, auto/crypto pages)

## Known leftovers

- SVG/CSS art, not photography.
- Other slot cabinets and poker engine remain atmosphere-only.
- Ambient audio still requires unmute; no looping beds.
- Browser back still only plays the `entering` veil (history is not intercepted).
