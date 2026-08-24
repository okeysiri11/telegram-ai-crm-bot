# SPRINT 50.0 PLAN — Crypto EUR/USD + DXY Market Intelligence

## Goal

Center Crypto OTC desk on **EUR/USD + DXY** market intelligence with real service boundaries, honest provider states, analytical signals (no trade execution), structured AI consensus, and Telegram calling the same backend as Web.

## Architecture

```
Web Crypto desk  ──┐
Telegram crypto  ──┼──► services/fx_market_intel (canonical)
                   └──► /api/crypto-mi/v1/fx-intel/*
```

Providers (pluggable):
- EUR/USD: NBU cross (live when reachable)
- DXY: stub until external index feed
- News / Macro calendar: null adapters (ingest/normalize/dedupe ready)
- Charts: existing chartProvider boundary + FX overlay when quote connected

## Non-goals

- Broker / trade execution
- Fabricated quotes, news, or macro events
- Changing Sprint 48 antifraud
- Postgres migration for analysis memory (in-process + hooks this sprint)

## Deliverables

See `docs/SPRINT_50_0_RESULT.md`.
