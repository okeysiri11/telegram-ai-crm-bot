# Sprint 22 — Odessa Prime immersive lobby and map

Play-money only. Lobby interior + interactive floor plan. Roulette/blackjack gameplay was not redesigned.

`REAL_MONEY_IMPLEMENTED=NO`  
`PAYMENTS_IMPLEMENTED=NO`

## Architectural decisions

- **Extend `src/web/src/casino/`.** Dedicated `assets/lobby.css` and `lobby/hotspots.ts`. No new `platform_*` package, no Three.js.
- **`CasinoBrowseRoute` for `/casino/*`.** Visual browse (facade, lobby, map, room shells) does not require login. PLAY still uses `CasinoGuestModal` + `loginRedirect(returnTo)`. CRM / owner / dashboard stay on `ProtectedRoute`.
- **Photographic lobby still** at `/assets/casino/lobby/hall.jpg` (not under `/casino/*`) so Render SPA catch-all cannot swallow it.
- **Shared hotspot catalog** drives hall overlays, map zones, and ИГРОВЫЕ ЗАЛЫ. Occupancy is not faked.

## What shipped

- Full-bleed grand hall with chandelier, columns, carpet, NPCs, gold hotspots and hover previews.
- ЗАЛ / КАРТА toggle; `/casino/map` is the same lobby scene in map mode.
- Architectural floor plan with clickable zones and «вы здесь» on lobby.
- CasinoShell: ГОРОД / КАЗИНО / АКЦИИ / ТУРНИРЫ / ПОДДЕРЖКА plus ЛОББИ / ИГРОВЫЕ ЗАЛЫ / VIP / БАР / РЕСТОРАН.
- Subtle lobby drone only after unmute. Default muted.
- Guest visual browse without dumping to `/` or `/login`.

## Intentionally deferred

- Roulette Royale cinematic table (Sprint 23)
- Blackjack table redesign
- Poker engine
- Payments

## Gates (local, pre-push)

- Targeted Sprint 22 tests: `casinoLobby.test.tsx` — 10 passed
- Casino regression: entrance + world + live + routes — 42 tests passed together with lobby
- `npx tsc -b --pretty false`: casino-new errors = 0 (pre-existing odessa3d / agro / crypto / hercules debt unchanged)
- `npx vite build`: pass (earlier this sprint)

## Production health at START_HEAD `99f691b1`

Inspected live before the lobby commit:

- `/liveness` HTTP 200 `status=alive` `startup_validated=false` (known pre-existing; not a Sprint 22 regression)
- `/readiness` HTTP 200 `ready=true` all checks healthy
- `/api/casino/v1/health` HTTP 200 play-money only

## Production Gate retrigger

GitHub Actions had a major outage on 2026-08-26. Run `32984612323` for `868e39e9` stayed `queued` with 0 jobs for ~3h after Actions returned to operational. This follow-up retriggers `Production Gate (develop)` so Render `checksPass` can deploy.

## Leftovers not in this commit

Uncommitted room-table visual immersion from an earlier attempt stays local (AmbientLayer, rooms-visual, table lamps, `casinoImmersion.test.tsx`, Sprint 21 immersion RESULT). Sprint 22 does not redesign roulette/blackjack gameplay.
