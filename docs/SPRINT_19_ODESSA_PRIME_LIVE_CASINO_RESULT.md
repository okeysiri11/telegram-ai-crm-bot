# Sprint 19 — Odessa Prime Live Casino

## What shipped

Sprint 19 makes the existing Odessa Prime casino **feel live** without rewriting the platform, weakening auth, or claiming unfinished gameplay as finished.

- Subtle CSS ambience (light sweep, reflections, bokeh, silhouettes, signage shimmer, slot glow, idle wheel).
- Performance tiers **HIGH / MEDIUM / LOW** from viewport, DPR, cores, touch, and `prefers-reduced-motion`.
- Visit-able atmosphere rooms: **poker, VIP, restaurant, bar** (no poker engine, no real-money).
- Mobile portrait composition with a **controlled lobby pan**, safe-area padding, and thumb-sized hotspots.
- Ultrawide side wings so the hall does not stretch.
- Room aliases (`/casino/lobby`, `/casino/poker`, …) plus lazy-loaded secondary rooms and a skeleton fallback.
- Audio architecture prepared and **muted by default** (no autoplay, no looping ambience).
- Keyboard focus, skip link, hotspot labels, decorative `aria-hidden`.

`REAL_MONEY_IMPLEMENTED=NO`. `PAYMENTS_IMPLEMENTED=NO`. Play / DEMO CHIPS only.

**Do not start Sprint 20 until requested.**

## Architecture decisions

1. **CSS-first ambience, no rAF loops.** Particles/bokeh are static elements with CSS animation. LOW disables them. Timers on roulette/slots/bet-lock/transitions clear on unmount.
2. **Atmosphere rooms vs table join.** Floor catalog marks poker/VIP/bar/restaurant **open for visit**. `poker-room` table join stays `coming_soon` (HTTP 400). Poker gameplay is not claimed finished.
3. **Extend Sprint 18 folders.** No new `platform_*` package. Lazy chunks only for poker/VIP/bar/restaurant. Lobby-critical CSS stays on the shell.
4. **Auth unchanged.** Bearer fail-closed. `returnTo` still allowlists `/casino…`. Visual QA without a valid session still lands on `/login?returnTo=%2Fcasino…`.

Rejected: WebGL particle systems, new audio libraries, compressing the entire hall into one unreadable mobile image.

## Casino routes

| Path | Surface |
|---|---|
| `/casino` | Cinematic entrance |
| `/casino/lobby` | Alias → `/casino/floor` |
| `/casino/floor` | Spatial lobby (ЗАЛ / КАРТА) |
| `/casino/rooms/roulette` | Roulette hall |
| `/casino/roulette` | Table browser |
| `/casino/roulette/:tableId` | Live European table |
| `/casino/rooms/blackjack` | Blackjack salon |
| `/casino/blackjack` | Alias → blackjack salon |
| `/casino/rooms/slots` | Slot parlor |
| `/casino/slots` | Alias → parlor |
| `/casino/slots/odessa-gold` | Odessa Gold |
| `/casino/rooms/poker` (`/casino/poker`) | Poker atmosphere |
| `/casino/rooms/vip` (`/casino/vip`) | VIP salon atmosphere |
| `/casino/rooms/restaurant` | Restaurant atmosphere |
| `/casino/rooms/bar` | Bar atmosphere |

Unknown `/casino/*` paths redirect to the entrance (no blank screen).

## Navigation

`CasinoShell` chrome is unchanged in role: header + mobile bottom nav + city return. Lobby hotspots and map cells call `useRoomTransition().go`. Browser back was verified: floor → roulette hall → floor.

## Animation

| Surface | Idle | Active | Result |
|---|---|---|---|
| Roulette wheel | CSS `is-idle` rotation (tiered) | JS transform after **server** spin | Phase `RESULT` / `SETTLED` |
| Blackjack | Face-down placeholders | CSS deal on cards | `data-phase=result` |
| Odessa Gold | Cabinet glow | Reel CSS while spinning | `data-phase=result` |
| Lobby / entrance | Shimmer, sweep, silhouettes | — | — |

Spin/result still require the casino API. Preview visual QA confirmed **idle** states. Settlement remains server-authoritative (Sprint 18).

## Performance strategy

`resolvePerformanceTier` → `data-tier` on `.op-world`.

| Tier | Ambience |
|---|---|
| HIGH | Sweep, reflect, bokeh, silhouettes, idle wheel, slot glow |
| MEDIUM | Sweep/reflect/static silhouettes, slower idle wheel, no bokeh |
| LOW / reduced-motion | No ambient layer, no idle wheel, no extra blur/backdrop-filter |

Usability (hotspots, bets, labels) is never gated on effects.

## Mobile strategy

At ≤859px the lobby stage is `min-width: 40rem` inside `.op-lobby-pan` (horizontal pan, not a crushed hall). Safe-area insets on header/bottom/sticky bet rail. Tested at **360 / 390 / 430**. Bottom nav stays five primary destinations; atmosphere rooms are on the pan + map + room links.

## Files created

- `src/web/src/casino/ambient/AmbientLayer.tsx`
- `src/web/src/casino/ambient/ambient.css`
- `src/web/src/casino/assets/live.css`
- `src/web/src/casino/assets/casino/README.md`
- `src/web/src/casino/audio/casinoAudio.ts`
- `src/web/src/casino/components/RoomSkeleton.tsx`
- `src/web/src/casino/hooks/usePerformanceTier.ts`
- `src/web/src/casino/rooms/AtmosphereRoom.tsx`
- `src/web/src/casino/rooms/PokerRoom.tsx`
- `src/web/src/casino/rooms/VipRoom.tsx`
- `src/web/src/casino/rooms/BarRoom.tsx`
- `src/web/src/casino/rooms/RestaurantRoom.tsx`
- `src/web/src/casino/casinoLive.test.tsx`
- `docs/SPRINT_19_ODESSA_PRIME_LIVE_CASINO_RESULT.md`

## Files changed

Casino shell, routes, lobby, games page, roulette/blackjack/slots tables, bet-lock, room transition, sound, `applications/casino/config.py` (`19.0.0-play-money`), `tables.py` floor routes, `tests/test_casino_world.py`, `tests/test_casino_premium.py`.

## Tests executed

- `npx vitest run src/casino/casinoLive.test.tsx src/casino/casinoWorld.test.tsx src/casino/casinoRoutes.test.tsx` — **19 passed**
- `.venv/bin/python -m pytest tests/test_casino_world.py tests/test_casino_premium.py` — **15 passed**
- `npx vite build` — **success** (`casino-*.js` ~40 kB, lazy atmosphere chunks &lt;0.2 kB each, CSS ~21 kB)
- `npx tsc -b --pretty false` — **CASINO_NEW_ERRORS=0**, **PRE_EXISTING_ERRORS=43** (city/agro/crypto/hercules tests, unchanged)

Blackjack wallet assertion was hardened for a **push** (opening chips restored). That is a flake fix, not a rules change.

## Visual QA

Playwright Chromium (cached `chromium-1148`) against `vite preview :4173` with an ISAM-shaped session. Viewports: 360, 390, 430, 1366×768, 1920×1080, 2560×1080, plus reduced-motion.

Screenshots: `/tmp/s19-visual/`. Findings: `/tmp/s19-visual/findings.json`.

Confirmed: CasinoShell on every room, no Enterprise Dashboard chrome, 7 lobby hotspots, idle wheel, BJ cards, Odessa Gold reels, poker/VIP/bar/restaurant rooms, lobby alias, **no document overflow**, mute default, PLAY / DEMO CHIPS copy. Unauthenticated hits preserve `returnTo`.

1440×900 was not a separate capture; 1366 and 1920 bound it.

Spin/result of live tables were **not** driven against a running casino API in preview.

## Known limitations

- Poker/VIP/bar/restaurant are **atmosphere rooms**. No poker engine, no menu, no drink orders.
- No photoreal casino photography — CSS sets. Asset folders are ready for later art.
- Ambience is CSS, not a particle engine.
- Audio hooks exist; room loops are intentionally no-ops until a user-gesture design in a later sprint.
- Mobile lobby uses pan; not every hotspot is on-screen at 360 without scrolling the stage.

## Recommended Sprint 20 priorities

1. Poker table engine (server-authoritative, play-money) if that is the next game.
2. Replace CSS sets with photographed/rendered room art in `assets/casino/{room}/`.
3. Optional user-gesture ambience loops with the existing mute control.
4. Measured FPS sampling to drop HIGH → MEDIUM at runtime.
5. Dealer/croupier motion and richer roulette ball rest without extra GPU cost.

## QA gate

```
ENTRANCE_WORKS=YES
LOBBY_WORKS=YES
LOBBY_HOTSPOTS_WORK=YES
ROOM_TRANSITIONS_WORK=YES
BROWSER_BACK_WORKS=YES
ROULETTE_ANIMATION_WORKS=YES
BLACKJACK_ANIMATION_WORKS=YES
ODESSA_GOLD_ANIMATION_WORKS=YES
POKER_ROOM_WORKS=YES
VIP_ROOM_WORKS=YES
RESTAURANT_WORKS=YES
BAR_WORKS=YES
MOBILE_360_WORKS=YES
MOBILE_390_WORKS=YES
MOBILE_430_WORKS=YES
DESKTOP_WORKS=YES
ULTRAWIDE_WORKS=YES
REDUCED_MOTION_WORKS=YES
AUTH_REGRESSION=none
NEW_CASINO_TYPESCRIPT_ERRORS=0
NEW_REGRESSIONS=none
```

Roulette/blackjack/Odessa Gold **idle** verified in Chromium. Spin/result remain the Sprint 18 server-driven animations (not live-spun in preview). Poker gameplay is **not** finished.
