# Sprint 20 — Odessa Prime luxury rooms

Play-money only. Extends Sprint 19. No real-money, no payments, no `/api/v1` or `/management/v1` changes.

## Architectural decisions

- **Keep browsing behind `ProtectedRoute`.** Unauthenticated navigation to `/casino/*` still goes to `/login?returnTo=<casino-path>` (not the enterprise homepage). Guest modal is for in-room PLAY actions that receive `401` (expired session / guest play).
- **Catch-all stays in the casino.** Unknown `/casino/*` paths render `CasinoUnknown`, they do not `Navigate` to the entrance. That was the bug that made `/casino/roulette/table/royale-1` look like the home page and ate `returnTo`.
- **Reuse Sprint 19 shell/scenes.** Visual rooms, ChipSelector, RoomNavigation, guest modal, and CSS composition extend the existing casino module. No new `platform_*` package.
- **Temporary art is SVG/CSS under `src/web/public/casino/`.** Photography can replace files without route changes.

## What shipped

- `/casino/roulette/table/royale-1` and `/casino/roulette/royale-1` open the **live roulette table**, not the entrance.
- Unauthenticated play actions open a **guest modal** with preserved `returnTo`.
- Blackjack is a felt salon: dealer, shoe, seat, chips, **СДАТЬ / ЕЩЁ / ХВАТИТ / УДВОИТЬ**. Double is server-authoritative.
- Bar / restaurant / VIP / poker are navigable visual rooms with **← В ЗАЛ / КАРТА / next room**.
- Hover/press/focus/disabled/loading on controls; lobby hotspot CTA appears on hover; winning roulette number highlights; chips lift + glow.
- Structured assets under `src/web/public/casino/{entrance,lobby,roulette,blackjack,poker,slots,vip,bar,restaurant,ui}/`.

## Routes

| Path | Surface |
|---|---|
| `/casino` | Cinematic entrance |
| `/casino/lobby`, `/casino/floor` | Visual lobby |
| `/casino/map` | Floor map |
| `/casino/games` | Game catalog |
| `/casino/roulette` | Roulette hall |
| `/casino/roulette/royale-1` | Live table |
| `/casino/roulette/table/royale-1` | Live table (alias) |
| `/casino/roulette/:tableId` | Table (`royale-1` / `roulette-royale-1` resolve to live) |
| `/casino/blackjack` | Blackjack salon |
| `/casino/poker` `/casino/vip` `/casino/bar` `/casino/restaurant` `/casino/slots` | Visual rooms |

Legacy `/casino/rooms/*` kept. Unknown casino paths stay inside the casino.

## Test / build

- `npx vitest run src/casino/casinoLive.test.tsx src/casino/casinoWorld.test.tsx src/casino/casinoRoutes.test.tsx` — **20 passed**
- `.venv/bin/python -m pytest tests/test_casino_world.py tests/test_casino_premium.py tests/test_casino_immersive.py tests/test_casino_foundation.py -q` — **28 passed**
- `npx vite build` — **success**
- `npx tsc -b --pretty false` — **CASINO_NEW_ERRORS=0**; **PRE_EXISTING_TSC=43** (ai-command, odessa3d, etc. — not this sprint)

## Known leftovers

- Other slot cabinets and poker engine remain atmosphere-only.
- SVG/CSS art, not photography.
- Ambient audio still requires unmute; no looping beds.
- Full-page casino browsing still requires login via `ProtectedRoute`; guest modal covers in-session `401` on PLAY actions.
