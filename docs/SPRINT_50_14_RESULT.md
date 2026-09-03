# Sprint 50.14 — FX production data reliability

## Goal

Stop EURUSD/DXY native charts from blanking on Yahoo HTTP 429, keep all seven timeframes renderable, and never mint fake OHLC or giant synthetic candles.

## Phase 1 — pipeline (audit)

UI `EurUsdNativeChart` / `DxyNativeChart` → `useFxNativeLiveChart` → `fetchFxCandles` → `/api/crypto-mi/v1/fx-intel/candles` → `FxMarketIntelService.candles()` → `candle_feed.get_candles()` → Yahoo (cached, single-flight) → `normalize_yahoo_bars` → Lightweight Charts `setData` / `update`.

Canonical symbols: `EURUSD` (`EUR/USD`) and `DXY`. React never talks to Yahoo.

### EURUSD Yahoo intervals

| TF | Yahoo interval | range | notes |
|---|---|---|---|
| 1m | 1m | 1d | native |
| 5m | 5m | 5d | native |
| 15m | 15m | 5d | native |
| 1h | 60m | 10d | native hourly |
| 4h | 60m | 30d | aggregated to 4h |
| 1D | 1d | 6mo | native |
| 1W | 1wk | 2y | native |

### DXY Yahoo intervals

Yahoo `DX-Y.NYB` has no true 1m/5m. Those requests use 60m/10d and `source_resolution` reports the actual median spacing. No fake 1m bars are manufactured from hourly history.

| TF | Yahoo interval | range | source_resolution |
|---|---|---|---|
| 1m | 60m | 10d | typically 60m |
| 5m | 60m | 10d | typically 60m |
| 15m | 15m | 5d | 15m when Yahoo supplies it |
| 1h | 60m | 10d | 60m |
| 4h | 60m | 30d | 4h after aggregate |
| 1D | 1d | 6mo | 1d |
| 1W | 1wk | 2y | 1w |

## Architectural decisions

- Extended `services/fx_market_intel` (`yahoo_feed` + new `candle_feed`) rather than a new platform package.
- Server TTL cache keyed by `symbol+timeframe`, last-good store that empty/error must never overwrite, single-flight coalescing, 429 cooldown (Retry-After or 30/60/120/300s).
- Provider interface: `get_candles` / `cached_quote`. Alternative candle provider is a one-env plug (`FX_CANDLE_PROVIDER` / FINNHUB / TWELVEDATA / POLYGON). No keys in repo → no invented credentials. NBU remains EURUSD **quote** fallback only.
- New live bucket: `open=high=low=close=quote` (Phase 8). Previous `open=last.close` created giant gap candles.
- Frontend: do not `setData([])` on TF change or on upstream error when last-good bars exist. Generation + abort + `safeUpdateCandlestick` from 50.13 kept.

## Alternative provider

- `ALTERNATIVE_PROVIDER_AVAILABLE=no`
- `ALTERNATIVE_PROVIDER_NAME=` (empty)
- `API_KEY_REQUIRED=yes` for a real second candle feed

## Tests

Backend: `tests/test_sprint_50_14_fx_reliability.py` (429→cache, empty does not wipe last-good, TTL, single-flight, OHLC, fallback hook).

Frontend: `src/web/workspace/crypto/sprint_50_14_fx_reliability.test.tsx` (EURUSD/DXY TF walks, rapid switching, 429 keep bars, `NO_GIANT_SYNTHETIC_CANDLE`).
