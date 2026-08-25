# Sprint 15 — Casino Foundation (play-money)

## Architecture

Casino is a **customer application / vertical** (`applications/casino`) on ADOS Platform Core.
It does not replace CRM, City, or Finance. It binds a city venue to a play-money lobby.

```
Enterprise City (building id: casino)
        ↓  /casino/venues/odessa-prime
Casino Lobby  /casino
        ↓
Venue + European Roulette demo
        ↓
Play-money wallet + append-only ledger  (PostgreSQL)
        ↓
Room presence foundation               (Redis, memory fallback)
```

Future regulated-money boundary (NOT implemented):

```
Casino Domain
      ↓
Player Account
      ↓
Compliance Gateway
      ├── Age verification
      ├── KYC
      ├── AML
      ├── Responsible gaming
      └── Geolocation
      ↓
Regulated Wallet
      ↓
Payment Provider
```

This sprint implements **none** of those layers. No payment form, no card fields, no deposit button.

## Routes

| Surface | Path |
|---|---|
| SPA lobby | `/casino` |
| SPA venue + roulette demo | `/casino/venues/:venueId` |
| SPA roulette alias | `/casino/venues/:venueId/roulette` |
| API | `/api/casino/v1/*` |
| City building | `casino` → `/casino/venues/odessa-prime` |

Public reads: `GET /health`, `/lobby`, `/venues`, `/venues/{id}`, `/roulette/rounds/{id}`, `/venues/{id}/rooms`.
Mutations and wallet/ledger require Bearer auth (production fail-closed).

## Database entities

Alembic `t9p012345678` (head after Sprint 14 `s8n901234567`):

- `casino_venues` — tenant-scoped venues bound to a city building id
- `casino_wallets` — one play-chip wallet per (tenant, player)
- `casino_ledger` — append-only chip movements, unique `(tenant_id, idempotency_key)`
- `casino_roulette_rounds` — server result + settled flag
- `casino_roulette_bets` — wagers with idempotency

## Wallet design

Currency code `CHIPS`. Opening grant 10_000 play chips on first wallet read. Integer only.
No deposit, withdraw, FX, or cash-out APIs.

## Ledger design

Every chip movement is an immutable ledger row. Duplicate keys are no-ops (idempotent).
Wagers debit before the spin; payouts credit `stake + profit` on win.

## Roulette design

European wheel 0–36. Server RNG (`secrets.randbelow` + entropy bytes). Clients cannot post
`result_number`. Second `POST .../spin` returns the same settled result (`duplicate_settlement_guard`).

## Multiplayer foundation

Redis set `casino:room:{tenant}:{venue}:members` with TTL. Memory fallback when Redis is absent.
Join / leave / presence only — not a full realtime game socket.

## Redis role

Presence + future pub/sub channel naming. PostgreSQL remains chip SoT. Redis is not a wallet.

## City venue binding

`CITY_BUILDINGS` id `casino` in the marketplace district. Search tokens include casino/roulette/odessa.
Command palette: Casino lobby + Odessa Prime. Desktop launcher includes Casino.

## Search integration

`src/web/navigation/managers/searchIndex.ts` documents plus `searchBuildings("casino")`.

## Security model

- Bearer required for wallet, ledger, bets, spin, room join/leave
- Tenant via principal or `X-Tenant-Id`
- Production rejects unverified Bearer (Sprint 14)
- Health/lobby payloads contain no secrets, URLs, or credentials
- No card PAN storage

## Production deployment

Same Render web service (`ados-web`). SPA deep links rely on `api/web_static.py` fallback.
Migrations run in `scripts/run_production_web.py`. `render.yaml` topology unchanged.

## Known limitations

- Single seeded venue (`odessa-prime`)
- Roulette demo only (no blackjack/slots)
- Redis presence is not a synced table animation
- Unauthenticated CRM list reads remain pre-existing debt (unchanged)
- Frontend `tsc` failures in unrelated verticals remain pre-existing

## Future regulated-money boundary

A later sprint may add a **Compliance Gateway** in front of a regulated wallet and a licensed
payment provider. That work must not be stubbed as a fake deposit UI. Play-money chips must
never be convertible in-app without an explicit licensed product and legal review.
