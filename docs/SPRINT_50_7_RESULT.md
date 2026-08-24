# Sprint 50.7 RESULT — Native DXY chart (Lightweight Charts)

**Status:** COMPLETE  
**Date:** 2026-08-12  
**Do not start the next sprint automatically.**

---

## Root cause

DXY was rendered with TradingView public embed `TVC:DXY`. That widget is frequently blocked/limited (login/popup, empty iframe). Sprint 50.5 showed an honest text fallback with Yahoo mid only — **no candle chart**. Backend already had real Yahoo OHLC bars (`DX-Y.NYB`) via `/fx-intel/candles`, but the Crypto workspace never rendered them for DXY.

---

## Old TVC:DXY behavior

- `TradingViewEmbed` mapped DXY → `TVC:DXY`
- After ~4s without iframe → static fallback card (“виджет недоступен”)
- Quote mid from Yahoo could show; **candles did not**
- Risk of broken TradingView popup / empty chart UX

---

## New DXY architecture

```
Yahoo Finance DX-Y.NYB
  → services/fx_market_intel/yahoo_feed.fetch_bars (normalize OHLC)
  → GET/POST /api/crypto-mi/v1/fx-intel/candles?symbol=DXY&timeframe=…
  → DxyNativeChart (lightweight-charts candlesticks, full width)
  → DualChartsPanel DXY card (TF buttons + live quote line)
```

EUR/USD keeps TradingView (`FX:EURUSD`). DXY **never** mounts TradingView.

Snapshot contract:

- `tradingview.DXY = null`
- `dxy_chart.engine = ados_lightweight_charts`

---

## Backend endpoint reused/created

**Reused (enhanced):**

- `GET|POST /api/crypto-mi/v1/fx-intel/candles`
- Provider: Yahoo (`DX-Y.NYB`)

**Response metadata (50.7):**

- `bars`, `bar_count`, `chart_ready`
- `provider`, `provider_symbol`
- `supported_timeframes`
- `last_close`, `last_bar_at`
- `chart_engine` (`lightweight_charts` for DXY)

**Snapshot additions:** `dxy_chart` block + honest `tradingview.DXY_note_ru`.

No new DB migration.

---

## Provider

| Item | Value |
|------|--------|
| Provider | Yahoo Finance |
| Symbol | `DX-Y.NYB` |
| Quote | `YahooQuoteProvider` / `GET …/quote?symbol=DXY` |

---

## Actual bars received (live local stack, 2026-08-12)

| Timeframe | status | bar_count | last_close |
|-----------|--------|-----------|------------|
| 15m | connected | **284** | ~99.873 |
| 1H | connected | **177** | ~99.873 |
| 4H | connected | **150** | ~99.873 |
| 1D | connected | **125** | ~99.873 |

Live quote: **connected** mid ≈ **99.874**

Evidence: `/tmp/sprint_50_7_bars.json`

---

## Supported timeframes

`15m`, `1H`, `4H`, `1D` (UI also exposes chart prefs `1m`/`5m`/`1W`; Yahoo map falls back to `1H` when unsupported).

---

## Frontend component

| File | Role |
|------|------|
| `src/web/workspace/crypto/DxyNativeChart.tsx` | Lightweight Charts candle renderer + candles fetch |
| `src/web/workspace/crypto/paperTradingPanels.tsx` | `DualChartsPanel` — DXY uses `DxyNativeChart`, EUR/USD keeps TV |
| dep | `lightweight-charts@4.2.0` |

Features: full-width ResizeObserver, TF refetch, live quote caption, no TV popup for DXY.

---

## Screenshots / manual verification notes

Automated UI screenshots not captured in this agent session. Manual check:

1. Open http://localhost:5180/workspace/crypto (demo `owner@demo.corp` / `demo`)
2. Charts view — DXY card shows candlesticks (`data-testid=dxy-native-chart`, engine `lightweight-charts`)
3. Switch 15m / 1h / 4h / 1D — bars reload; quote line shows Yahoo mid
4. Confirm **no** TradingView iframe/popup under DXY (only EUR/USD uses TV embed)
5. API sanity: `curl 'http://127.0.0.1:8080/api/crypto-mi/v1/fx-intel/candles?symbol=DXY&timeframe=1H'` → `chart_ready: true`, `bar_count > 0`

---

## Tests

**Backend:** `tests/test_sprint_50_7_dxy_native_chart.py` — TF normalize, bar normalize, fetch metadata, HTTP candles + snapshot  
**Frontend:** `sprint_50_7_dxy_native_chart.test.tsx` — candle mapping, DualCharts mounts native DXY (not TV), TF buttons, live quote line  

**Regression (targeted, green):**

- `test_sprint_50_6_paper_persist`, `test_sprint_50_5_operator_desk`, `test_crypto_tx_antifraud_48_0`
- FE: `sprint_50_0`, `50_5`, `50_6`, `50_7` vitest files

---

## Localhost status (left running)

| URL | Status |
|-----|--------|
| http://127.0.0.1:8080/health | 200 |
| http://localhost:5180/ | 200 |
| http://localhost:5180/login | 200 |
| http://localhost:5180/workspace/crypto | 200 |

Logs: `/tmp/ados_api_50_7.log` · Vite PID retained on `:5180`

---

## Remaining provider limitations

- Yahoo rate limits / outages → `chart_ready: false` with RU error (no fabricated bars)
- Intraday DXY coverage depends on Yahoo futures session hours; some bars may be flat/low volume
- `1m` / `5m` / `1W` UI chips are not first-class Yahoo ranges for DXY (normalize to nearest supported / default `1H`)
- EUR/USD still depends on TradingView public widget (unchanged)
- No TradingView login / paid data feed in this sprint

---

## Architectural decisions

1. **Extend existing candles API** — do not invent a second market-data engine.
2. **Native chart for DXY only** — avoid swapping DXY for another TV symbol; remove broken `TVC:DXY` from the operator path.
3. **Yahoo remains the honest provider** already used for DXY quotes since 50.1.
