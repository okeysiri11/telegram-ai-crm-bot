# Sprint 50.8 RESULT — Native EURUSD chart (Lightweight Charts)

**Status:** COMPLETE  
**Date:** 2026-09-03  
**Do not start the next sprint automatically.**  
**Do not commit / do not push** (this sprint).

---

## Goal

Replace the TradingView EUR/USD widget (`FX:EURUSD`) with the same native Lightweight Charts path already used by DXY.

## Architecture

```
Yahoo Finance EURUSD=X
  → services/fx_market_intel/yahoo_feed.fetch_bars
  → GET /api/crypto-mi/v1/fx-intel/candles?symbol=EUR/USD&timeframe=…
  → EurUsdNativeChart (lightweight-charts)
  → DualChartsPanel EUR/USD card
```

DXY stays on `DxyNativeChart` + Yahoo `DX-Y.NYB`. Shared helpers live in `fxNativeChartCore.ts` without rewriting the DXY component.

## Timeframes (EURUSD)

| UI | Yahoo interval | Range | Notes |
|----|----------------|-------|--------|
| 1m | 1m | 1d | real bars |
| 5m | 5m | 5d | real bars |
| 15m | 15m | 5d | real bars |
| 1h | 60m | 10d | real bars |
| 4h | 60m | 30d | real 1h aggregated to 4h OHLC |
| 1D | 1d | 6mo | real bars |
| 1W | 1wk | 2y | real bars |

DXY still reports `15m / 1H / 4H / 1D`. Unknown DXY TFs keep the previous 1H fallback so the DXY chart does not regress.

## Snapshot / contracts

- `tradingview.EUR/USD = null`
- `eurusd_chart.engine = ados_lightweight_charts`
- `eurusd_chart.yahoo_symbol = EURUSD=X`
- Quote source label on the live desk: `Yahoo Finance (EURUSD=X)` (NBU is not shown when Yahoo is primary)

## Architectural decisions

- **Extend `yahoo_feed` + DualCharts**, do not add a new platform package.
- **Copy DXY chart component to `EurUsdNativeChart`** instead of merging both into one `FxNativeChart` this sprint — avoids DXY regression.
- **Do not delete `TradingViewEmbed.tsx`**: other tests still document `tvSymbolFor`; EURUSD rendering no longer mounts it.

## Tests

- `tests/test_sprint_50_8_eurusd_native_chart.py`
- `src/web/workspace/crypto/sprint_50_8_eurusd_native_chart.test.tsx`
- DXY regression: `tests/test_sprint_50_7_dxy_native_chart.py`, `sprint_50_7_dxy_native_chart.test.tsx`

## Live verification (2026-09-03, `/workspace/crypto?view=charts`)

| Check | Result |
|-------|--------|
| EURUSD quote | `1.1601` · `yahoo_eurusd` · live · Yahoo Finance (EURUSD=X) |
| Last candle close | `1.16009` |
| Price difference | `0.00001` |
| Native chart | Lightweight Charts, all TFs ready (1m 440 … 1W 106 bars) |
| TradingView | not mounted; error copy absent |
| DXY | native, 195 bars, Yahoo DX-Y.NYB |
| Quote poll | fetched_at advanced after 30s |

**pytest:** 32 passed (`50.0`/`50.1`/`50.7`/`50.8`)  
**vitest:** 11 passed (`50.7`+`50.8`); related `50.1`/`50.2`/`50.3`/`50.5` passed  
**build:** `npx vite build` succeeded (tsc -b not run — unrelated project TS debt)
