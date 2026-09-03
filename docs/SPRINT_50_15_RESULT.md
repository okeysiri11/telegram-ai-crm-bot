# Sprint 50.15 — EURUSD chart stability v2

## Goal

Fix the FX data pipeline (not CSS candle width): 1m dash-like artifacts, false 4h (60m relabel), timeframe-switch series/scale leak, Yahoo 429 blanking after Render restart.

## Root cause

1. **1m dashes.** Two stacked defects: (A) Yahoo quote-only rows were filled as `o=h=l=c`, producing consecutive flat bars; (B) 700+ 1m bars were fitted into the viewport so even real pip bodies collapsed into horizontal marks. Live quote overlay was not rewriting older history; the forming bucket update was already last-bar-only.
2. **Timeframe corruption.** Each displayed TF was requested independently from Yahoo. 4h used native 60m bars and labeled them 4h. Switching 1m → 4h → 1h reused the same Lightweight Charts candlestick series and autoscale, so the previous TF’s scale/state leaked.

## Architectural decisions

- Extended `services/fx_market_intel` (no new platform package). Canonical bars + local aggregator in `bars.py`. Persistent last-good in `last_good_store.py` using **Redis when `REDIS_URL` is set**, else process memory. Repo is Postgres-only; SQLite is not used.
- EURUSD bases: **1m** and **1h**. Derive 5m/15m from 1m; **4h always from 1h**; 1D from 1h when ≥20 daily buckets, else native 1d; 1W from 1D.
- DXY 1m/5m return `UNAVAILABLE_AT_SOURCE_RESOLUTION` (no fake minute bars from 60m). 4h/1D/1W aggregate from DXY 1h.
- Yahoo circuit breaker: CLOSED → OPEN on 429 with 60/120/300/600s backoff, HALF_OPEN probe, global lock so chart clicks do not stampede Yahoo.
- UI: chart instance persists; **candle series is recreated per timeframe generation**. Viewport policy 100/100/100/90/80/90/70. `barSpacing=6`, `minBarSpacing=3`. No `fitContent()`. Status shows LIVE/CACHED/RATE LIMITED plus Provider / Base / Display / Bars / Updated, and `60m -> aggregated 4H` when derived.
- Dual charts warm only EURUSD 1m + 1h and DXY 1h.

## Intentionally deferred

- A second candle vendor (Finnhub/TwelveData/Polygon) still has no keys. Quote fallback remains NBU for EURUSD only.
- Redis last-good is best-effort: if Redis is down, memory cache still works for the process lifetime.

## Tests / build

- Backend: `tests/test_sprint_50_15_fx_stability.py` + 50.14/50.7 FX files — pass.
- Frontend: vitest `sprint_50_11`–`50_15` FX files — pass.
- `src/web` `npx vite build` — pass.
