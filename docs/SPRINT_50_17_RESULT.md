# Sprint 50.17 — DXY intraday hard fix (1m / 5m / 15m)

## 1. ROOT CAUSE

1. **Backend refused real DXY 1m/5m.** `get_candles("DXY", "1m"|"5m")` short-circuited to `UNAVAILABLE_AT_SOURCE_RESOLUTION` and labeled `base_resolution=60m`. `_TF_MAP_DXY` mapped 1m/5m onto Yahoo interval `60m`. Yahoo `DX-Y.NYB` **does** return native 1m (median Δ=60s) and 5m (Δ=300s) when those intervals are requested — they were never asked for.
2. **UI showed `60m -> aggregated` with Bars: 0** because the unavailable pack lied about source resolution.
3. **Giant 15m rectangle:** when history was empty/unavailable, the chart seeded a **single candle from the live Yahoo quote** (`applyQuoteToActiveCandle(null, quote)` + `Баров: live`). One bar filled the viewport. Stale higher-TF series was also left in place if unavailable did not `setData([])`.

This was not a Lightweight Charts width bug.

## 2. FILES CHANGED

- `services/fx_market_intel/bars.py` — `can_aggregate` / `source_covers_target`
- `services/fx_market_intel/yahoo_feed.py` — DXY 1m/5m native intervals
- `services/fx_market_intel/candle_feed.py` — DXY resolver, downsample guard, v2 cache keys for DXY 1m/5m/15m
- `services/fx_market_intel/last_good_store.py` — DXY intraday last-good keys `v2`
- `src/web/workspace/crypto/fxNativeChartCore.ts` — quote without history → no candle
- `src/web/workspace/crypto/useFxNativeLiveChart.tsx` — clear series on unavailable; no live-seed
- `src/web/workspace/crypto/DxyNativeChart.tsx` / `EurUsdNativeChart.tsx` — source metadata
- tests: `tests/test_sprint_50_17_dxy_intraday.py`, `src/web/workspace/crypto/sprint_50_17_dxy_intraday.test.tsx`, plus 50.11/13/14/15/16 updates
- `docs/SPRINT_50_17_RESULT.md`

EUR/USD 1m router (Dukascopy → last-good → Yahoo line) is unchanged.

## 3. ARCHITECTURE

DXY:

- **1m:** Yahoo `DX-Y.NYB` interval `1m` range `1d`. If detected spacing is coarser than 1m → unavailable. Never 60m fallback.
- **5m:** native 5m, else aggregate **1m → 5m**.
- **15m:** native 15m, else 5m→15m, else 1m→15m.
- **1H / 4H / 1D / 1W:** previous working path (60m/1h native + up-aggregation only).

`can_aggregate(source, target)` is true only when source seconds < target seconds and target % source == 0.

## 4. DXY MATRIX (resolver policy)

| TF | provider | source resolution | transformation | status |
|---|---|---|---|---|
| 1m | yahoo DX-Y.NYB | 1m | native | HEALTHY or controlled unavailable |
| 5m | yahoo | 5m or 1m | native or aggregated 1m→5m | HEALTHY or unavailable |
| 15m | yahoo | 15m / 5m / 1m | native or finer→15m | HEALTHY or unavailable |
| 1H | yahoo | 60m | native | existing |
| 4H | yahoo | 60m | aggregated 60m→4H | existing |
| 1D | yahoo | 60m or 1d | aggregate or native daily | existing |
| 1W | yahoo | 1d | aggregated daily→1W | existing |

## 5. BUG FIX — giant candle

Live quote no longer creates a historical bar when `last` is null. Unavailable/empty history calls `setData([])` and disables live series updates. Quote stays in the quote line only.

## 6. RACE CONDITION

Unchanged generation / AbortController / series recreate per TF. Unavailable now clears the series so a previous 1H dataset cannot remain under a 15m/1m button.

## 7. TESTS

Backend 50.14–50.17 and frontend 50.7/11/13–17 FX files.

## 8. EUR/USD REGRESSION

`test_eurusd_1m_router_untouched` plus 50.15/50.16: Dukascopy 1m still wins; Yahoo 1m not called when Dukascopy is HEALTHY.

## 9. DEPLOY

Commit hash filled after push.
