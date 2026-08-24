# SPRINT 50.1 RESULT — Crypto Live Intelligence Runtime

## Runtime status

- Local stack scripts: `scripts/run_fx_intel_stack.sh` / `scripts/stop_fx_intel_stack.sh`
- Backend: `scripts/run_api_local.py` → `:8080`
- Frontend: `src/web` `npm run dev` → `:5180`
- Both left running after sprint completion (when stack start succeeds)

## TradingView status

**Connected as public widget** (`FX:EURUSD`, `TVC:DXY`). No TradingView login/password stored. No private TV API credentials.

## EUR/USD provider

- Spot: **НБУ cross** (EUR/UAH ÷ USD/UAH) when reachable
- OHLC bars / TA: **Yahoo Finance `EURUSD=X`**
- Explicit error/needs_config when unavailable — no fabricated mids

## DXY provider

- Quote + bars: **Yahoo Finance `DX-Y.NYB`**
- Honest status when Yahoo rate-limits or fails

## News sources

- Curated allowlisted RSS: **Federal Reserve** + **ECB**
- Normalize + dedupe + AI-оценка heuristics (not trade advice)
- Persisted to `fx_mi_news_items` when Postgres available

## Macro sources

- Public FairEconomy / Forex Factory weekly JSON
- Soft-fail on HTTP 429/errors (empty calendar + status message)
- Persisted to `fx_mi_macro_events`

## Persistence

- Alembic `y8s901234567` → tables `fx_mi_*`
- Repository `repositories/fx_market_intel_repository.py`
- Analysis runs, agent outputs, consensus, signals, news, macro, evaluations
- Fallback to in-process memory if DB unavailable
- Upgrade/downgrade: downgrade is non-destructive; upgrade is idempotent via `to_regclass`

## AI specialists

- Operational cards; **Запустить** runs shared `FxMarketIntelService` pipeline
- Gaps listed when sources missing; confidence haircut applied

## Consensus

- Weighted Chief consensus stored with agent votes
- UI vote panel renders **only stored run output**

## Signals

- Generated only from completed analysis runs
- `analytics_only=True`, `trade_execution=False`
- Linked to `analysis_run_id` when persisted

## Scheduler

- Wired into existing `pg_scheduler_engine`:
  - `fx.intel.morning` / `pre_europe` / `pre_us` / `evening`
  - `fx.intel.evaluate` (1h/4h/1d outcome fill when later bars exist)
- No second scheduler implementation

## Telegram

- Commands: EURUSD, DXY, Утренний обзор, Анализ сейчас, Новости, Календарь, Сигналы (+ legacy aliases)
- Calls `telegram_brief()` → same service as Web

## Tests

| Suite | Result |
|-------|--------|
| `tests/test_sprint_50_0_fx_market_intel.py` | passed |
| `tests/test_sprint_50_1_fx_live_intel.py` | passed |
| Sprint 48 antifraud / payout | passed (targeted) |
| FE `sprint_50_0` + `sprint_50_1` desk tests | run in sprint |

## New regressions

None in targeted FX + antifraud suites after route `{run_id}` f-string fix and macro soft-fail.

## Pre-existing failures

Unrelated `src/web` lint/typecheck noise from earlier modules may still exist outside crypto desk tests.

## Credentials still required

- Optional paid market-data / news wires for higher quality & rate-limit headroom
- Notification channel credentials for delivery
- No TV credentials required for public widget

## Production blockers

- Yahoo / FairEconomy rate limits (429) under heavy load
- Multi-pod requires Postgres (memory fallback is single-process)
- Scheduler jobs must be seeded via `SchedulerEngineV1.ensure_default_jobs`
- Evaluation quality depends on bar availability after horizons

## Implemented vs deferred

### Implemented
- TradingView public embeds for EUR/USD + DXY
- Live DXY (Yahoo) + EUR/USD NBU spot + Yahoo bars
- Curated news + macro calendar adapters
- Durable `fx_mi_*` persistence + evaluation hooks
- Real analysis pipeline + specialists + consensus UI
- News / Calendar / History nav
- Scheduler job keys
- Telegram shared path
- Antifraud untouched

### Not implemented / limited
- Paid institutional data feeds
- Guaranteed calendar availability under 429
- Full MFE/MAE path reconstruction beyond available bars
- Push notification delivery channels

## Manual verification URLs

- Frontend: http://localhost:5180
- Login: http://localhost:5180/login (`owner@demo.corp` / `demo`)
- Crypto: http://localhost:5180/workspace/crypto
- EUR/USD graph: http://localhost:5180/workspace/crypto?view=charts (select EUR/USD, 1H)
- DXY graph: same → select DXY
- Analyses: `?view=analysis`
- AI specialists: `?view=specialists`
- Signals: `?view=signals`
- News: `?view=news`
- Calendar: `?view=calendar`
- Settings: `?view=settings`
- Backend health: http://127.0.0.1:8080/health
- FX health: http://127.0.0.1:8080/api/crypto-mi/v1/fx-intel/health

## Click path

1. Login → Crypto OTC  
2. Графики → EUR/USD → 1H → confirm TradingView renders  
3. Select DXY → confirm TradingView renders  
4. Анализы → Утренний обзор → Запустить анализ → inspect sources / votes / consensus  
5. История анализов → open saved snapshot  
6. Новости / Календарь / Сигналы / AI-специалисты / Настройки  

## Next recommended sprint

**Sprint 50.2** (do not auto-start): rate-limit resilient paid providers, notification delivery, richer evaluation paths — still no trade execution.
