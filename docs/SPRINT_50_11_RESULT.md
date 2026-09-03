# Sprint 50.11 RESULT — Live tick + active candle update (EURUSD / DXY)

**Status:** COMPLETE  
**Date:** 2026-09-03

## Problem

Native Lightweight Charts for EUR/USD and DXY rendered on production but looked static. Quote polling updated caption text only. Historical candles loaded on mount / timeframe change. `series.update()` was never called.

## Audit (production 2026-09-03 ~07:07 UTC)

| | EURUSD | DXY |
|--|--|--|
| QUOTE_ENDPOINT | `GET /api/crypto-mi/v1/fx-intel/quote?symbol=EUR/USD` | `GET /api/crypto-mi/v1/fx-intel/quote?symbol=DXY` |
| CANDLES_ENDPOINT | `GET /api/crypto-mi/v1/fx-intel/candles?symbol=EUR/USD&timeframe=` | `GET .../candles?symbol=DXY&timeframe=` |
| Quote poll (before) | 15_000 ms | 15_000 ms |
| Candle poll (before) | none | none |
| Quote changing (3× ~8s) | no (`1.1616` ×3, `fetched_at` advanced) | yes (`99.272` → `99.274` → `99.270`) |
| 1m active bucket | `07:07:00Z` | `07:07:00Z` |
| Last candle | `07:06:53Z` close `1.161575` | `06:57:18Z` (Yahoo 1m DXY falls back; last bar `1H`) |
| Active 1m candle exists | no | no |

Root cause **D**: Lightweight Charts received data only on timeframe change / page load. Quotes never painted the active candle.

## Architecture

```
Yahoo quote (EURUSD=X / DX-Y.NYB)
  → GET /fx-intel/quote (5s poll, exclusive in-flight)
  → applyQuoteToActiveCandle(timeframe bucket)
  → Lightweight Charts series.update(candle)

Yahoo historical bars
  → GET /fx-intel/candles
  → setData() on mount / TF change
  → silent refresh every 60s for 1m / 5m / 15m only
```

Do not refetch 1000+ historical candles on every quote tick.

## Architectural decisions

- Extend `fxNativeChartCore.ts` + shared `useFxNativeLiveChart` instead of duplicating overlay logic in EURUSD and DXY charts.
- Bucket comparison uses timeframe floors so Yahoo 1m bars with seconds (e.g. `07:06:53`) update in-place when the quote is still in that minute, and append a new bucket when the clock rolls.
- New-candle OHLC uses previous close as open and `max/min(open, quote)` for high/low so the bar stays valid without inventing prices.
- EURUSD Yahoo `mid` format is `.5f` (was `.4f`) so live ticks are not rounded to `1.1616`.
- Rejected: polling the candles endpoint every 5s (Yahoo throttle + full redraw).

## Polling

- `FX_QUOTE_POLL_MS = 5000`
- Historical refresh: 60s for 1m/5m/15m; otherwise only on timeframe change
- Overlapping quote polls skipped (`quotePollInFlight`)
- History fetch uses AbortController; interval cleared on TF change / unmount
- If Yahoo historical bars are empty, the first real quote still seeds the active candle (`series.update`). No invented prices.

## Production verify (2026-09-03)

`/workspace/crypto?view=charts` after SHA `66667097` then follow-up empty-history seed.

EURUSD 1m: `Updated` advanced every ~5s (`10:24:48` → `10:25:08`). Close moved `1.15770` → `1.16120` when Yahoo quote changed. LIVE ● visible. 5m retained polling.

DXY: quote poll ~5s; `Updated` advanced; mid moved `99.255` → `99.252`. First DXY 1m history fetch during warmup returned 0 bars; empty-history seed covers that without refetching full history every tick.

Candle endpoint was called on timeframe change only (4 fetches in ~40s), not on every quote tick.

