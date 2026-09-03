# Sprint 50.13 — timeframe switch crash fix

## ROOT_CAUSE

On timeframe change the live-quote overlay called `series.update()` before the new history replaced the old series.

Example EURUSD `1m → 5m` at 08:47:23:

- last 1m bar time = `08:47:00`
- 5m live bucket = `08:45:00`
- `08:45:00 < 08:47:00` → Lightweight Charts throws
  `Cannot update oldest data, last time=[object Object], new time=[object Object]`
  and the Crypto Charts ErrorBoundary fires.

The `[object Object]` text is LWC stringifying internal time points; the failure is chronological `update()`, not a new chart engine.

The same race hits DXY: a live 1m candle can sit ahead of coarser Yahoo fallback bars, then a 5m bucket is older than that live bar.

## Fix

- Canonical `normalizeChartTime()` → Unix seconds for every historical and live bar (1D/1W included). No mixed BusinessDay/unix series.
- Per-chart generation id: increment on timeframe/symbol change; abort previous candle request; ignore stale callbacks.
- Clear series + last timestamp + active candle before loading the new TF (`ACTIVE_BUCKET_RESET`).
- Live `series.update` only after that generation’s history is applied, via `safeUpdateCandlestick` (append / same-ts update / drop older, try/catch isolation).
- History: sort, dedupe equal timestamps, reject invalid times. No `time+1` invention.

Yahoo providers, 5s quote poll, autoscale, last-price line/label, live-follow, and paper/analysis/signal buttons are unchanged.

## Tests

`src/web/workspace/crypto/sprint_50_13_fx_timeframe_switch.test.tsx`

- EURUSD and DXY 1m↔5m, full TF walk, late HTTP callback, rapid switch without waiting.
- Monotonic series mock throws the production error if an old timestamp is applied.
