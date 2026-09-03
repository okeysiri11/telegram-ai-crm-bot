# Sprint 50.12 RESULT — Live chart visibility (autoscale + follow)

**Date:** 2026-09-03

## Audit (before)

Shared hook `useFxNativeLiveChart` created both EURUSD and DXY charts.

| | EURUSD | DXY |
|--|--|--|
| AUTOSCALE | LWC default (no scaleMargins) | same |
| VISIBLE_BARS 1m/5m | full history via `fitContent()` | full history via `fitContent()` |
| PRICE_SCALE_MARGIN_TOP | unset | unset |
| PRICE_SCALE_MARGIN_BOTTOM | unset | unset |

`fitContent()` ran on first load and timeframe switch only — **not** on quote ticks.  
`setVisibleRange` / `setVisibleLogicalRange` were not used.  
`applyOptions({ priceScale })` was not used.

That made EURUSD 1m look static: hundreds of bars stretched the price scale across the whole session.

## Change

- Initial / TF-switch viewport: last 120 (1m/5m/15m), 100 (1h/4h), 90 (1D), 70 (1W) bars via `setVisibleLogicalRange`. History is kept.
- Right scale: `autoScale: true`, margins `0.12 / 0.12`.
- Stronger last-price line and label (`priceLineWidth: 2`, teal `#0f766e`).
- LIVE follow by default; user pan disables snap; **К текущей цене** restores.
- Quote ticks still only `series.update()` — no `fitContent()` per tick, no fake prices.

## Architectural decisions

- Viewport helpers live in `fxNativeChartCore.ts`; behavior stays in the shared hook (no duplicate EURUSD/DXY logic).
- Rejected `fitContent()` on live ticks (would fight user zoom).
- Rejected a hardcoded EURUSD min/max (would distort scale).
