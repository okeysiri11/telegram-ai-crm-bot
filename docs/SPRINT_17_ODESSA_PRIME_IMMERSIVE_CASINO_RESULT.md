# Sprint 17 — Odessa Prime immersive casino

## Architecture

Sprint 17 is a **visual and navigation layer** on the Sprint 15–16 play-money vertical
(`applications/casino`, `/api/casino/v1`). Wallet, ledger, demo grant, server RNG, Redis
presence, city venue binding, and Bearer fail-closed auth are reused.

```
Enterprise City  →  /casino  (CasinoShell, no FullLayout)
        ↓
Entrance  /  Floor 2.5D  /  Games  /  Roulette tables
        ↓
/casino/roulette/roulette-royale-1
        ↓
Server open → bets → spin  →  client wheel/ball animates to server number
        ↓
PostgreSQL ledger settlement (unchanged)
```

**Decision:** CSS 2.5D hall + SVG/CSS wheel, not a new Three.js asset pipeline.
Three.js already exists for Odessa 3D City and was not loaded on casino routes.

**No Alembic migration.** Round `opened_ts` / phase live in existing round payload JSON.

`REAL_MONEY_IMPLEMENTED=NO`. `PAYMENTS_IMPLEMENTED=NO`.

## UX implemented

- **CasinoShell** — Odessa Prime chrome (logo, Город, Казино, Акции, VIP, Турниры,
  Поддержка/history, PLAY HUD, avatar, sound mute, back to city). Hides enterprise FullLayout.
- **Entrance** `/casino` — cinematic hall, chandeliers, marble, depth tables, HUD stats,
  ВОЙТИ В КАЗИНО / ВЫБРАТЬ ИГРУ / ВЕРНУТЬСЯ В ГОРОД.
- **Floor** `/casino/floor` — spatial zones + ЗАЛ/КАРТА toggle.
- **Games** `/casino/games` — visual cards; roulette LIVE, others SOON.
- **Tables** `/casino/roulette` — Royale 1 live; Classic / Monaco / VIP SOON.
- **Table** `/casino/roulette/:tableId` — wheel, ball, European board, chips, seats, phases.
- History drawer: ВСЕ / СТАВКИ / ВЫИГРЫШИ / ДЕМО-ФИШКИ.
- Sound manager default **muted** (Web Audio beeps, no binary assets).
- Mobile: compact header, bottom nav, scrollable felt, sticky controls.

## Routes

| Path | Surface |
|---|---|
| `/casino` | Entrance |
| `/casino/floor` | Hall + map |
| `/casino/games` | Game selector |
| `/casino/roulette` | Table browser |
| `/casino/roulette/roulette-royale-1` | Live table |
| `/casino/venues/odessa-prime` | Redirect → `/casino` |
| `/casino/venues/:id/roulette` | Redirect → Royale 1 |

## Roulette

Server remains authoritative (`secrets.randbelow`). Client **never** posts `result_number`.
Flow: confirm bets → `spin` → animate wheel/ball **toward the returned number** → HUD/ledger.

Added even-money **low/high** and 2:1 **dozen/column**. Split/street/corner are not faked.

Phases (server `opened_ts` + client sequence): BETTING_OPEN → CLOSING → NO_MORE_BETS →
SPINNING → RESULT → SETTLED.

Chips: 10 / 50 / 100 / 500 / 1000 / 5000 PLAY. Actions: ОЧИСТИТЬ / ПОВТОРИТЬ / УДВОИТЬ /
СДЕЛАТЬ СТАВКУ.

## Auth returnTo

`ProtectedRoute` stores a sanitized internal path (query + sessionStorage + location state).
`LoginPage` uses `resolvePostLoginPath` so casino deep links return to the same table.
Open redirects (`https:`, `//`, `javascript:`) are rejected.

## City

Войти в казино → `/casino`. Вернуться в город → `/enterprise-city?building=casino` (2D focus only).
**Odessa 3D mesh was not remapped.**

## Tests

- `tests/test_casino_foundation.py` / `test_casino_premium.py` / `test_casino_immersive.py`
- `src/web/src/casino/casinoRoutes.test.ts` — routes, returnTo, floor/table render
- Production gate includes immersive pytest

## Frontend gate

`npx vite build` — casino lazy chunk (~25 kB JS + 10 kB CSS), not on CRM pages.

Sprint 17 casino TypeScript: **zero** after fixing CasinoShell `loc` leftover.
Pre-existing `tsc -b` debt remains in Odessa3D / Agro / Hercules / crypto / AI Command.

## Production

Recorded after push: Render `revision` must equal `HEAD` on `develop`.
Public: `https://ados-web.onrender.com/casino` and
`https://ados-web.onrender.com/casino/roulette/roulette-royale-1`.
Anonymous mutations still 401.

## Next

Do **not** start Sprint 18 until requested. Stay play-money only.
