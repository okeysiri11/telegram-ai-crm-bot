# Sprint 50.16 — Market Data Provider V2 (EURUSD real 1m OHLC)

## Goal

Stop rendering Yahoo EURUSD 1m quote-only bars as candlesticks. Yahoo `EURUSD=X` 1m is quote-only (`open == high == low == close`), which Lightweight Charts correctly draws as horizontal dashes. Do not invent wicks. Serve genuine 1m OHLC when a legal server-side source exists; otherwise show a **DEGRADED_LINE** price trace with an explicit badge.

## Phase 1 — provider audit (no secrets)

| PROVIDER_NAME | CONFIGURED | API_KEY_AVAILABLE | EURUSD_1M_SUPPORTED | DXY_SUPPORTED |
|---|---|---|---|---|
| Yahoo | yes | n/a | no (quote-only 1m) | 15m/60m/1d; 429-prone; no true 1m |
| NBU | yes (public) | n/a | no (quote/reference only) | no |
| Dukascopy public ticks | yes (HTTP datafeed, no key) | n/a | yes (tick → true 1m OHLC) | no (exact ICE DXY not confirmed) |
| Twelve Data | env name only | no | if keyed | unknown |
| Finnhub | env name only | no | if keyed | unknown |
| Polygon / Massive | env name only | no | if keyed | unknown |
| Alpha Vantage | no | no | — | — |
| Tiingo | no | no | — | — |
| Marketstack | no | no | — | — |
| Financial Modeling Prep | no | no | — | — |
| OANDA | no | no | — | — |
| FXCM | no | no | — | — |
| Stooq | no | no | — | — |
| TradingView | no | n/a | not a backend provider | not used |

TradingView widgets/pages are not a backend source. NBU is never used as minute history.

## Architectural decisions

- Extended `services/fx_market_intel` (no new `platform_*` package). `MarketDataProvider` gained `get_candles` / `health` / `capabilities`. Canonical bars only; provider payloads never reach the SPA.
- **EURUSD 1m router:** keyed provider (if a real API key exists) → Dukascopy tick OHLC → persistent **real** last-good → degraded Yahoo (line only).
- Dukascopy is a documented HTTP tick datafeed (`datafeed.dukascopy.com/.../h_ticks.bi5`), not HTML scraping. Hour files fetch in parallel with a 12s per-hour / 16s overall budget so the SPA 20s timeout is not exceeded. The unpublished current hour is skipped.
- Quality scoring: Yahoo-flat (`zero_range_ratio >= 0.80`) is **DEGRADED** and cannot beat a HEALTHY real-OHLC provider. HEALTHY 1m requires `real_body_bars > 10` and `real_wick_bars > 5` on the last 120 bars (unless the sample is genuinely too small).
- Redis / memory keys distinguish `fx:last_good:{symbol}:{resolution}:real` vs `:degraded`. Degraded Yahoo must not overwrite real last-good.
- Live quote (Yahoo/NBU) may update only the **active** bucket: `high=max`, `low=min`, `close=quote`. Closed history is never rewritten with flat Yahoo bars.
- 5m/15m still aggregate from the 1m base; 1h/4h/1D/1W keep the 50.15 Yahoo-60m + local aggregate path (no independent Yahoo call per TF).
- Display: `CANDLES` when real OHLC exists; `DEGRADED_LINE` (Lightweight Charts line series) when only quote-only 1m exists. Badge: `DEGRADED DATA — Источник дает только минутные ценовые точки без полного OHLC`.
- DXY: no exact DXY/USDX/DX instrument on Dukascopy was verified. `DXY_SOURCE_UNAVAILABLE=yes` for 1m/5m. Do not substitute another dollar index. Higher TFs remain Yahoo 60m when that source works.

Rejected: manufacturing wicks from Yahoo flats; scraping TradingView; using NBU as 1m history; treating Yahoo 1m as HEALTHY candles.

## Intentionally deferred

- Authenticated Twelve Data / Finnhub / Polygon remain adapters-only until keys exist in the environment. No credentials were invented.
- True 1m DXY remains unavailable at source.

## Tests / build

- Backend: `tests/test_sprint_50_16_fx_provider.py` + 50.14 / 50.15 FX files.
- Frontend: vitest `sprint_50_16_fx_provider.test.tsx` (line vs candles + rapid TF including mode switch) plus prior 50.11–50.15 FX files.
- `src/web` `npx vite build`.

Production PASS requires deployed SHA verification of EURUSD 1m: either real candles (`provider=dukascopy`, `REAL_BODY_BARS>10`, `REAL_WICK_BARS>5`) or a clean line + DEGRADED DATA badge — never a field of dash candlesticks.
