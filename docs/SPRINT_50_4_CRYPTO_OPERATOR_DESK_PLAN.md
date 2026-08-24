# Sprint 50.4 — Analysis Pipeline & Operator Desk Depth (Plan)

## Goal

Complete the operator analysis loop: market data → specialists → Chief consensus → persisted result view, honest scheduler next-run, contextual empty states, Russian UI. No Sprint 50.5. No real broker.

## Architecture

| Area | Approach |
|------|----------|
| Final bias | Extend `build_consensus` → `BUY_BIAS` / `SELL_BIAS` / `NEUTRAL` / `WAIT` + bullish/bearish/neutral scores |
| Risk Agent | Add to `run_full_analysis` agent chain |
| Result view | Expand `AnalysisResultPanel` + CTAs |
| Scheduler | Read real `fx.intel.*` jobs; never invent next run |
| Empty states | `emptyDescription` on cabinet sections; no demo CTA copy in crypto |

## Out of scope

Model training, broker execution, Sprint 50.5.
