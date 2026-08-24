# Sprint 50.2 — Crypto Operator Desk Depth (Plan)

## Goal

Make Crypto EUR/USD + DXY desk operationally coherent: dual charts, runnable analyses/agents, signals with triggers, calendar links, **paper** trading (simulation), trade journal, and entity cross-links. No real broker execution. No model training.

## Architecture decisions

| Decision | Choice | Rejected |
|----------|--------|----------|
| Paper trading | Simulated fills from live/available quotes inside `fx_market_intel` | Broker / OTC payout wiring |
| Persistence | Extend `fx_mi_*` Postgres + memory fallback | New platform package |
| Cross-links | Shared IDs + `?view=&id=` deep links | Isolated pages |
| Signals | Analytics + optional price trigger; paper link only | Auto live execution |
| Training | Out of scope | Agent model training |

## Delivery

1. Paper engine + journal + signal trigger helpers
2. Migration/repo/handlers
3. Dual charts + paper/journal UI + cross-links (RU)
4. Tests + RESULT + stack restart
