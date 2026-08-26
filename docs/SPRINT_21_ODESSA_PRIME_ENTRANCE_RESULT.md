# Sprint 21 — Odessa Prime cinematic entrance

Play-money only. Facade / entrance / enter-transition only. Lobby, roulette, blackjack, poker, slots, bar, restaurant, and VIP were **not** redesigned.

`REAL_MONEY_IMPLEMENTED=NO`  
`PAYMENTS_IMPLEMENTED=NO`

## Architectural decisions

- **Extend `src/web/src/casino/`.** Tokens `--casino-*` live on `.op-root` (aliases of the Odessa Prime palette). Dedicated `assets/entrance.css` is the facade system. No new `platform_*` package, no Three.js, no video background.
- **Keep `/casino` as the canonical entrance** and `/casino/lobby` as the enter target. React Router table is additive: `/casino/promos`, `/casino/tournaments`, `/casino/support` render an in-casino «Скоро» page. Catch-all remains `CasinoUnknown` («Зал не найден»).
- **Photographic still + CSS/SVG planes.** `public/casino/entrance/facade.jpg` (~440 KB) is the building. Wet pavement, red carpet, chandelier pool, and door glow are CSS layers with light parallax. Rejected: multi-megabyte PNG, Three.js, and leaving `hall.svg` as the hero (it read as a schematic interior).
- **Enter CTA is local cinema, then `navigate(/casino/lobby)`.** Zoom + door brighten + gold/dark veil ~980 ms. Reduced motion skips the veil. Does not stack the shared room-transition leave timer.
- **LIVE ИГРОКИ / JACKPOT are isolated presentation figures** (`ENTRANCE_PRESENTATION`), not production telemetry. DEMO БАЛАНС reads the existing play-money wallet.

## What shipped

- CasinoShell product nav: ГОРОД · КАЗИНО · АКЦИИ · VIP · ТУРНИРЫ · ПОДДЕРЖКА. HUD: PLAY, muted sound, История, avatar, В ГОРОД. No ADOS CRM chrome on `/casino/*`.
- Full-viewport night facade on `/casino` with left copy, gold **ВОЙТИ В КАЗИНО**, three glass status panels, six artwork preview cards.
- Hover / press / focus on the enter CTA; click runs the cinematic enter into the existing lobby.
- Unimplemented cards (LIVE КАЗИНО, ТУРНИРЫ) open a polished «Скоро» modal. Live cards route to roulette / blackjack / poker / slots.
- Sound stays **muted by default**. Hover / click / door hooks exist; no autoplay, no missing asset URLs.
- Auth `returnTo` unchanged (`sanitizeReturnTo` / `loginRedirect`). Owner demo account not weakened.

## Test / build

- `npx vitest run src/casino/casinoEntrance.test.tsx src/casino/casinoWorld.test.tsx src/casino/casinoLive.test.tsx src/casino/casinoRoutes.test.tsx src/auth/demoOwnerAuth.test.tsx` — **45 passed**
- `npx vite build` — **success** (`casino-*.css` 44.5 kB, `casino-*.js` 51.1 kB gzip 14.4 kB)
- `npx tsc -b --pretty false` — **CASINO_NEW_ERRORS=0**; pre-existing debt remains in odessa3d / agro / crypto / hercules
- Playwright visual pass on 1920×1080, 2560×1080, 1440×900, 390×844: facade photograph visible, CTA live, soon modal, enter veil → lobby

## Intentionally deferred

- Lobby redesign
- Roulette / blackjack / poker / slots / bar / restaurant / VIP visual rebuilds
- Real ambience beds (architecture only; unmute required)
- Photographic art for the six preview cards (SVG artwork this sprint)
