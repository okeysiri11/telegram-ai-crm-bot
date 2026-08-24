# Sprint 50.4 — RESULT

## Scope

Analysis pipeline completion: Market data → agents → Chief consensus → persisted final bias result; analysis result view; active toggle; honest scheduler next-run; contextual empty states; cross-links; Russian operator UI. **No Sprint 50.5. No real broker.**

## CHART ACTIONS

**DONE** — Создать сигнал / К анализу / Бумажная торговля on dual charts (`data-testid` chart-signal|analysis|paper).

## SIGNALS

**DONE** — create from chart/analysis; list in Signal Center; enable/disable via `POST /fx-intel/signals/lifecycle`; row actions → paper / history.

## SIGNAL ENGINE

**DONE** — analytics-only; BUY_BIAS/SELL_BIAS added; price trigger; lifecycle ACTIVE/DISABLED; no trade execution.

## AI SPECIALISTS

**DONE** — Technical / DXY / Macro / News / Session / **Risk** / Chief; Run Now + settings; agent history empty copy.

## AGENT SETTINGS

**DONE** — localStorage agent settings persist (weight/instruments/enabled).

## ANALYSES

**DONE** — presets Morning / Before Europe / Before USA / Evening (+ others); Run Now; result panel; history.

## ANALYSIS SETTINGS

**DONE** — [Выключить]/[Включить] persists `enabled`, UI shows **Активен** / **Выключен** immediately.

## ANALYSIS PIPELINE

**DONE** — chain includes Risk Agent; consensus `final_result` ∈ {BUY_BIAS, SELL_BIAS, NEUTRAL, WAIT}; confidence; bullish/bearish/neutral scores; key_reasons; data_gaps; sources; persisted via existing `persist_full_analysis`.

## ANALYSIS RESULT VIEW

**DONE** — Общий вывод, Уверенность, EUR/USD, DXY, Технический анализ, Макро, Новости, Корреляция, Риск, Сессия, Что изменилось, Data gaps; buttons Создать сигнал / Открыть историю / Бумажная торговля.

## SCHEDULER

**DONE** (honesty) — `GET /fx-intel/schedule` reads real `fx.intel.morning|pre_europe|pre_us|evening` jobs. UI shows `next_run_at` only if present; else **«Автозапуск не настроен»**. No fabricated times.

**PARTIAL** — enabling a preset does not create/pause DB scheduler rows (platform jobs remain system-seeded); UI active flag is prefs-persisted.

## PAPER TRADING LINKS

**DONE** — chart / analysis / signal / result → `?view=paper`.

## CROSS LINKS

**DONE** — Chart↔Signal/Analysis/Paper; Analysis↔Signal/Paper/History; Agent↔Analysis/Signal/History; Signal↔Paper/History.

## EMPTY STATES

**DONE** — contextual RU copy for signals / agent history / analysis history / paper; cabinet `emptyDescription` avoids forcing «Создайте первую запись или загрузите демо-данные» when overridden.

## LOCALIZATION

**DONE** — operator strings Russian; allowed product names retained (TradingView, EUR/USD, DXY, RSI/MACD/EMA/SMA/ATR, agent names).

## TESTS

| Suite | Result |
|-------|--------|
| `tests/test_sprint_50_4_analysis_pipeline.py` | PASSED |
| `tests/test_sprint_50_0` … `50_3` + antifraud 48.0 | PASSED (targeted) |
| `src/web/.../sprint_50_4_analysis_pipeline.test.ts` | PASSED |

## LOCALHOST

Restart via `scripts/stop_fx_intel_stack.sh` / `scripts/run_fx_intel_stack.sh`, with Vite held on a durable shell (script nohup can die with parent). **Re-verified 2026-08-12:**

| URL | Status |
|-----|--------|
| `http://127.0.0.1:8080/health` | **200** |
| `http://localhost:5180/` | **200** |
| `http://localhost:5180/login` | **200** |
| `http://localhost:5180/workspace/crypto` | **200** |

Manual API checklist: signal create → list → disable lifecycle → Technical Agent → Morning (`SELL_BIAS` + scores/reasons/gaps/sources, persist `postgres`) → schedule honesty «Автозапуск не настроен» → history → paper 200.

Tests re-run: pytest 50.4 **7 passed**; vitest 50.4 **8 passed**.

Services left running (API PID `/tmp/ados_api_50_4.pid`, Vite `/tmp/ados_web_50_4.pid`).

## Architectural decisions

1. Extend `build_consensus` with `final_result` + scores rather than a new package.
2. Keep legacy `overall_direction` as WATCH_* alias for older callers.
3. Schedule honesty endpoint reads `ScheduledJobRepository` directly (no fake clock).

## KNOWN DEBT

- Enable analysis ≠ mutate scheduler job enabled flag in Postgres.
- Manual browser click-through (steps 1–20) should be confirmed by operator in UI after restart.
- Full-repo `tsc` still has pre-existing errors outside crypto desk.

## STOP

Sprint 50.4 complete. **Do not start Sprint 50.5.**
