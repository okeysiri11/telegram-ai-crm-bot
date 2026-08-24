# SPRINT 50.0 RESULT — Crypto EUR/USD + DXY Market Intelligence

## Implemented

- Canonical `services/fx_market_intel` (symbols, providers, TA, correlation, news dedupe, macro model, signals, consensus, memory)
- HTTP `/api/crypto-mi/v1/fx-intel/*` (snapshot, quote, run, signals, news, macro, memory, technical, correlation)
- Crypto desk UI centered on EUR/USD + DXY (default watchlist, analyses presets, specialists dashboard, signals table, settings health)
- Chart workspace timeframe selector + honest provider/quote overlay
- Structured Chief Market Analyst consensus (weighted, not text concat)
- Signal engine analytics-only (`trade_execution=False`)
- News normalize + dedupe; macro calendar empty-state adapter
- Analysis memory records with pending evaluation hooks (no fake outcomes)
- Telegram: `💵 Курсы` shows EUR/USD+DXY via same service; commands prepared for morning/pre-trade/signals/news
- User-facing copy without engineering jargon; compact AI disclaimer
- Sprint 48 antifraud untouched; regression re-run green

## Not implemented

- Live DXY index feed
- Live TradingView widget embedding
- Wired economic-calendar vendor
- Wired news wire vendor
- Canonical scheduler auto-delivery of analyses
- Evaluation jobs filling 1h/4h/1d outcomes from historical market data
- Postgres durability for analysis/signal store

## Real providers connected

- **EUR/USD:** NBU cross (EUR/UAH ÷ USD/UAH) when bank.gov.ua reachable
- **OTC USDT/UAH:** existing dealer path (Telegram rates screen)

## Providers still required

- DXY index provider
- TradingView (or chart market-data) credentials
- News API / feed
- Macro economic calendar API
- Notification channels for scheduled delivery

## TradingView status

**Не подключено** (bridge/status only; no live widget).

## Market-data status

EUR/USD: **live NBU cross when online**, else error/not connected.  
DXY: **needs_config**.  
No fabricated mids.

## News status

Adapter + dedupe ready; default provider **not_connected**; empty feed (no fake articles).

## Macro-calendar status

Model + empty-state; provider **not_connected** (no fake CPI/Fed rows).

## AI agent status

Specialist run + Chief consensus via `FxMarketIntelService.run_specialist`. Honest dependency gaps when quotes/calendar missing.

## Signal-engine status

Operational analytics entities; **cannot** execute trades.

## Persistence status

- Watchlist/analyses/specialist prefs: browser localStorage (tenant-scoped keys v50)
- Analysis/signal memory: in-process service store + evaluation hooks
- Antifraud: Postgres (unchanged)

## Tests

| Suite | Result |
|-------|--------|
| `tests/test_sprint_50_0_fx_market_intel.py` | passed (with antifraud combo: 42 passed) |
| FE `sprint_50_0_fx_desk.test.ts` + 49.x cabinets | 11 passed |
| Sprint 48 antifraud regression | green |

## New regressions

None in targeted suites.

## Pre-existing failures

Unrelated `npm run lint` noise in ai-command/hercules tests (from earlier sprints).

## Technical debt

- In-memory analysis/signal store
- DXY/news/macro/TV still external
- Scheduler not wired
- Outcome evaluation jobs not scheduled

## Production blockers

External credentials for DXY, news, calendar, TradingView; durable persistence for multi-pod; scheduler for delivery.

## Next recommended sprint

**Sprint 50.1 — Provider wiring:** connect DXY feed + optional TradingView/chart data + news/calendar adapters with health in Settings; persist analyses to platform memory/Postgres; do **not** enable trade execution.

Do **not** start automatically.
