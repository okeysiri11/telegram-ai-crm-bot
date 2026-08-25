# Sprint 16 — Premium play-money casino UX

## Architecture

Sprint 16 extends the Sprint 15 Casino vertical (`applications/casino`) and the `src/web/src/casino` SPA.
No new platform package, no competing API prefix, no regulated-money stack.

```
Enterprise City (building id: casino)
        ↓  «Войти в казино» → /casino
Premium lobby (spatial floor map)
        ↓  ROULETTE live / other areas «Скоро»
Venue floor + Redis table presence
        ↓  /casino/venues/{slug}/roulette
European roulette table (server RNG)
        ↓
PLAY / DEMO CHIPS wallet + append-only ledger (PostgreSQL)
```

Decision: **extend Sprint 15 APIs** (`/api/casino/v1/*`) instead of adding `/api/casino` without a version.
Rejected: a new WebSocket game server — production-safe casino WS is not present; HTTP + Redis presence is reused.

No Alembic migration. Demo-grant cooldown and table catalog are derived from existing `casino_ledger` rows and in-process/Redis membership. PostgreSQL remains chip source of truth.

## UX implemented

- Casino interior lobby: RECEPTION, BAR, ROULETTE, BLACKJACK, POKER, SLOTS, VIP
- Roulette is the live destination; others show **Скоро**
- Currency copy is **PLAY** or **DEMO CHIPS** only (no $, €, ₽, withdraw, deposit-as-money)
- **Получить демо-фишки** — server-fixed grant, cooldown, balance cap
- Ledger/history: timestamp, operation, wager, win/loss, delta, resulting balance
- Table presence: СТОЛ / ИГРОКИ / МЕСТА / СТАТУС, display names `Player NNN`
- Chip picker + betting felt + server spin
- City inspector primary CTA **Войти в казино**
- Loading, empty, error, reconnect, auth-required states
- Reduced-motion and visible focus on floor cards/chips

## Routes

| Surface | Path |
|---|---|
| SPA lobby | `/casino` |
| SPA venue floor | `/casino/venues/:venueId` |
| SPA roulette | `/casino/venues/:venueId/roulette` |
| City building | `casino` → venue deep link; enter CTA → `/casino` |

SPA fallback (`api/web_static.py`) is unchanged. Direct refresh of `/casino` and `/casino/venues/odessa-prime` remains valid.

## City integration / venue binding

- Building id `casino`, district `marketplace`, route `/casino/venues/odessa-prime`
- Search: `казино`, `рулетка`, `casino`, `odessa`
- Inspector: **Войти в казино** navigates to `/casino`
- Quick actions: lobby, venue card, roulette
- `MANUAL_ODESSA_ENTITY_MAP` is still empty — no GLB remapping

## Roulette architecture

Unchanged math from Sprint 15: European 0–36, `secrets.randbelow`, clients cannot post `result_number`.
UI now places a chosen chip + bet type (straight / red / black / even / odd), then `open → bet → spin`.
Second spin still returns `duplicate_settlement_guard`.

## Wallet / ledger / demo grant

Opening grant 10_000 PLAY chips on first wallet read (Sprint 15).

Sprint 16 adds `POST /api/casino/v1/wallet/demo-grant`:

- Amount is **server-fixed** (`demo_grant_chips = 5000`)
- Client `amount` / `balance` fields are rejected
- Cooldown 900s from last `demo_grant` ledger row
- Cap at 25_000 PLAY — no client-side balance invention
- Idempotency key `demo_grant:{tenant}:{player}:{window}`

Ledger items expose `operation`, `wager`, `win_loss`, `balance_delta`, `resulting_balance` and omit `player_id`.

## Multiplayer / presence

Redis set `casino:room:{tenant}:{venue}:{room_id}:members` (TTL 3600), memory fallback.
Default live table `roulette-royale` (6 seats). Coming-soon tables cannot be joined.
Join is idempotent (`reconnected: true`). UI rejoins on `visibilitychange` / `online` when seated.
Display identities are hashes (`Player 184`); emails, tokens, and raw player keys are not returned.

## Security

- Mutations + `/wallet` + `/ledger` + `/wallet/demo-grant` require Bearer
- Production fail-closed Bearer verification is unchanged
- Tenant isolation via principal / `X-Tenant-Id`
- Player identity no longer taken from a `token` claim
- Health/lobby/presence payloads contain no BOT_TOKEN, DATABASE_URL, Redis credentials, or hostnames

`REAL_MONEY_IMPLEMENTED=NO`. `PAYMENTS_IMPLEMENTED=NO`.

## Tests

- `tests/test_casino_foundation.py` — Sprint 15 regression
- `tests/test_casino_premium.py` — lobby floor, venue search including «казино», demo grant + cooldown, roulette settlement, presence join/leave/reconnect, display names, tenant isolation
- `src/web/src/casino/casinoRoutes.test.ts` — routes + PLAY copy
- `src/web/src/enterprise-city/cityCore.test.ts` — «казино» search + enter CTA
- Production gate includes both casino pytest files

## Frontend quality gate

`npx vite build` passes. Casino ships as a lazy chunk (`casino-*.js` + `casino-*.css`).

Sprint 16 TypeScript errors in casino files: **zero**.

Pre-existing `tsc -b` debt (unchanged, not caused by Sprint 16):

- `src/ai-command/*` (node types in tests, Badge tone)
- `src/enterprise-city/odessa3d/*` (node types, Three.js dispose, test doubles)
- `src/hercules/hercules_control_center.test.ts`
- `workspace/agro/*`
- `workspace/auto/AutoBusinessPage.tsx`
- `workspace/crypto/chartProvider.ts`

## Production verification

Verified 2026-08-25 against public `https://ados-web.onrender.com`:

| Check | Result |
|---|---|
| Git | `cafdcd9d2db29966e995035335101ca8a861c426` on `develop`, local=remote |
| GitHub Production Gate | success |
| Render `revision` | `cafdcd9d2db29966e995035335101ca8a861c426` |
| `/liveness` | `alive`, `startup_validated=true` |
| `/readiness` | `ready`, database healthy |
| `GET /api/casino/v1/health` | `16.0.0-play-money`, PLAY / DEMO CHIPS, postgres |
| Lobby / venue search «казино» | Odessa Prime bound to city building `casino` |
| SPA HTML | `/`, `/enterprise-city`, `/casino`, `/casino/venues/odessa-prime`, roulette deep link |
| Anonymous wallet / demo-grant | 401 Authentication required (no auth bypass) |
| Rooms | Redis backend, Roulette Royale 0/6 |

Authenticated PLAY wager/ledger smoke requires a real session (production Bearer is fail-closed; demo `Bearer test` is CI-only). Anonymous path correctly shows login/401 instead of inventing a client balance.

## Visual QA notes

Desktop and mobile layouts use CSS/SVG-free felt (CSS grid), chip buttons ≥ 44px on small screens,
horizontal felt scroll instead of page overflow, and no video/WebGL in the casino chunk.
City bundle was not given new 3D/video assets.

## Known pre-existing debt

- Unauthenticated Auto CRM list reads still return empty collections
- Free Render cold start
- `tsc -b` failures listed above
- Blackjack / poker / slots remain «Скоро»
- Presence is HTTP+Redis, not a realtime wheel animation

## Next recommended work

Do **not** start real-money, payments, KYC, or AML.
Sprint 17 candidates (if requested): extra live tables, richer seat UX, responsible-play session limits on PLAY chips only.
