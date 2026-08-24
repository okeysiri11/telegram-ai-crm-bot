# Sprint 50.1 — Crypto Live Intelligence Runtime (Plan)

## Goal

Make EUR/USD + DXY market intelligence **operational on localhost**: real charts (TradingView public embed), real quotes/bars where available, curated news + macro calendar from genuine public sources, durable Postgres persistence, runnable analysis pipeline with Chief consensus, analytics-only signals, Telegram on the same service path.

## Architecture decisions

| Decision | Choice | Rejected |
|----------|--------|----------|
| Chart rendering | TradingView **public widget** (no API key, no stored credentials) | Scraping TV private API |
| DXY + OHLC bars | Yahoo Finance chart API (`DX-Y.NYB`, `EURUSD=X`) | Stooq CSV (404 from this network) |
| EUR/USD spot | Keep NBU cross as primary; Yahoo as bar feed for TA | Fabricated mid |
| News | Curated RSS: Federal Reserve + ECB (allowlisted hosts only) | Arbitrary user URL fetch |
| Macro calendar | FairEconomy / Forex Factory weekly JSON (public) | Fake CPI/Fed rows |
| Persistence | New `fx_mi_*` tables + repository; extend `memory.py` | Second ORM / in-process-only |
| Scheduler | Extend `pg_scheduler_engine` DEFAULT_JOBS | New APScheduler package |
| AI | Same `FxMarketIntelService` specialists + weighted consensus | Duplicate TG/Web AI logic |
| Trades | Signals remain `analytics_only` / `trade_execution=False` | Broker wiring |

## Delivery slices

1. Migration + models + repository
2. Yahoo / RSS / macro providers + candles
3. Full analysis pipeline + evaluation hooks + scheduler jobs
4. TradingView widget + News/Calendar/History/Consensus UI
5. Telegram command aliases + tests + RESULT

## Security

- Tenant-scoped analysis/signals/config
- No secrets in frontend
- Allowlisted news hosts only
- Compact disclaimer; no trade execution
