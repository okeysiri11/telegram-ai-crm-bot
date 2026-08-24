# SPRINT 50.2 RESULT — Crypto Operator Desk Depth

## DUAL CHARTS

Side-by-side EUR/USD + DXY TradingView embeds with shared timeframe, quote integrity notes, and **Создать сигнал** per chart. Widget availability does not imply backend quote availability.

## MY INSTRUMENTS

Watchlist persistence (tenant-scoped localStorage) retained; defaults EUR/USD + DXY.

## ANALYSES

Presets + **Запустить анализ** → full pipeline; CrossLinkBar on analyses view.

## AI SPECIALISTS

Run Now retained; **Настроить** persists agent settings (`ados_otc_agent_settings_v52`).

## CHIEF ANALYST

Structured weighted consensus UI unchanged; covered by tests.

## SIGNALS

- Auto from analysis runs (analytics-only)
- Manual/chart create via `POST /fx-intel/signals`
- Optional price trigger (fires flag only — no trade execution)
- Links to analysis / paper

## CALENDAR

Macro events with links → Анализ / Сигнал / Бумажная сделка.

## PAPER TRADING

Simulation only (`paper=True`, `trade_execution=False`):
- market / limit
- SL / TP auto-check on refresh
- manual close + PnL
- API `/fx-intel/paper`
- Tables `fx_mi_paper_orders`, `fx_mi_paper_positions`

## JOURNAL

On position close: entry, exit, PnL, duration, signal, analysis, consensus slot, notes, market context.  
`training_enabled=False` — no model training.

## CROSS LINKS

`CrossLinkBar` + entity IDs across charts, analysis, specialists, signals, calendar, paper, journal, history.  
API `GET /fx-intel/links`.

## DATA PROVIDERS

No fake live mids. Integrity copy: «Источник недоступен» / «Нет данных» / «Данные неполные».

## TESTS

| Suite | Result |
|-------|--------|
| `tests/test_sprint_50_2_operator_desk.py` | passed |
| Sprint 48 antifraud (targeted with 50.2) | passed |
| FE `sprint_50_2_operator_desk.test.ts` (+ 50.0/50.1) | run at sprint end |

## LOCALHOST

Restarted API + frontend. Final verified HTTP:

| URL | Status |
|-----|--------|
| `http://127.0.0.1:8080/health` | **200** |
| `http://127.0.0.1:8080/api/crypto-mi/v1/fx-intel/health` | **200** |
| `http://127.0.0.1:8080/api/crypto-mi/v1/fx-intel/paper` | **200** |
| `http://localhost:5180/` | **200** |
| `http://localhost:5180/login` | **200** |
| `http://localhost:5180/workspace/crypto` | **200** |

PIDs (listeners): API **76589**, Vite **76605**. Both left **RUNNING**.

Start/stop: `scripts/run_fx_intel_stack.sh` / `scripts/stop_fx_intel_stack.sh`

## TECHNICAL DEBT

- Paper/journal primarily in-process with Postgres persist best-effort
- Limit fill / SL-TP evaluated on refresh, not tick stream
- Agent weight UI is shallow (persisted settings, not full weight editor)
- FairEconomy calendar may 429

## NEXT RECOMMENDED SPRINT

**Sprint 50.3** (do not auto-start): durable paper ledger UI polish, notification on trigger fire, richer agent weight editor — still no real broker execution.
