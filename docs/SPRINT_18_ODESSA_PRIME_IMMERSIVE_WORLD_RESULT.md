# Sprint 18 — Odessa Prime immersive world

## Architecture

Sprint 18 extends the Sprint 15–17 play-money vertical (`applications/casino`,
`/api/casino/v1`, `src/web/src/casino`). Wallet, ledger, demo grant, roulette RNG,
Redis presence, city binding, and Bearer fail-closed auth are reused.

```
Enterprise City → /casino (CasinoShell, no FullLayout)
        ↓
Cinematic entrance → spatial lobby (hotspots) → room transition
        ↓
/casino/rooms/roulette | blackjack | slots
        ↓
Server-authoritative settlement (Postgres ledger)
```

**Decision:** split the SPA into `components/`, `scenes/`, `rooms/`, `games/`,
`transitions/`, `audio/`, `assets/`, `hooks/`, `state/` instead of growing one
React tree. Backend games live as `applications/casino/blackjack.py` and
`applications/casino/slots.py`. Game session JSON reuses
`casino_roulette_rounds.payload` — **no Alembic migration**.

`REAL_MONEY_IMPLEMENTED=NO`. `PAYMENTS_IMPLEMENTED=NO`.

## UX

- Cinematic entrance `/casino`
- Lobby room with glowing hotspots + ЗАЛ/КАРТА
- Room transitions (veil overlay, same chrome)
- Roulette hall + dealer Victoria + European wheel/ball + chip flight + bet lock
- Blackjack salon + dealer Marina + dealing cards + HIT/STAND
- Slot parlor + Odessa Gold 5-reel machine
- Auth `returnTo` for new room/slot paths
- City return `/enterprise-city?building=casino`

## Routes

| Path | Surface |
|---|---|
| `/casino` | Entrance |
| `/casino/floor` | Lobby hall + map |
| `/casino/rooms/roulette` | Roulette hall |
| `/casino/roulette/roulette-royale-1` | Live table |
| `/casino/rooms/blackjack` | Blackjack salon |
| `/casino/rooms/slots` | Slot parlor |
| `/casino/slots/odessa-gold` | Odessa Gold |

## Games (server authority)

Roulette unchanged: `secrets.randbelow`, client cannot post `result_number`.

Blackjack: 6-deck shoe, hit/stand, 3:2 natural, dealer stands on 17. Clients cannot
post cards. Deal replay is idempotent by `idempotency_key`.

Odessa Gold: 5×3 reels, five lines, server strip + weights. Clients cannot post
reels. Duplicate `idempotency_key` returns the same grid and payout.

Wagers debit PLAY chips transactionally; payouts credit the same ledger.

## Tests

- `tests/test_casino_foundation.py` / `premium` / `immersive` / `world`
- `src/web/src/casino/casinoRoutes.test.tsx` / `casinoWorld.test.tsx`

## Frontend gate

`npx vite build` — casino lazy chunk (~35 kB JS + 16 kB CSS).

Sprint 18 casino TypeScript: **zero**. Pre-existing `tsc -b` debt remains outside casino.

## Visual QA

Inspected rendered preview (`vite preview :4173`) with Chromium at 1920×1080,
2560×1080, and 390×844. Session injected so ProtectedRoute served casino chrome.

Confirmed: cinematic entrance, lobby as a room with four hotspots, roulette dealer +
wheel + ball, blackjack dealer + cards, Odessa Gold reels, no WorkspaceLayout,
PLAY / DEMO CHIPS copy. Wheel/ball/reel/card motion is CSS after the **server**
payload; live spin against production API is gated by Bearer (anonymous 401).

## Production

Recorded after push: Render `revision` must equal `HEAD` on `develop`.

## Next

Do **not** start Sprint 19 until requested. Stay play-money only.
