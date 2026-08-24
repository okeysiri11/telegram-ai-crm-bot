# Sprint 50.5 — RESULT

## 1. Что обнаружено до изменений

После 50.4: анализ/сигналы/paper работали, но расписание UI не писало timezone/время; «Настроить» у специалистов почти no-op; chart CTA «К анализу»/«Бумажная торговля» были текстовыми ссылками; R/R в paper не считался; Risk Agent не валидировал paper; DXY TV без честного fallback; idempotency paper отсутствовал.

## 2. Root causes неработающих кнопок

| Кнопка | Причина |
|--------|---------|
| Настроить (specialist) | Только локальный stamp enabled/weight без формы параметров |
| Настроить расписание / Включить автозапуск | UI `enabled` не вызывал schedule API |
| Создать сигнал (полноценно) | Только one-shot WAIT без формы kind/condition/sound |
| Chart secondary CTAs | `Link` underline вместо primary Button |

## 3. Backend модели/сервисы

- `services/fx_market_intel/schedule.py` — timezone-aware configs + next/last run
- `services/fx_market_intel/specialist_settings.py` — defaults per agent
- `services/fx_market_intel/paper_trading.py` — `reward_risk` + `validate_risk_agent`
- `services/fx_market_intel/desk_ops.py` — idempotency keys, risk warnings, notifications on open
- Existing `consensus.py`, `signals.py`, `FxMarketIntelRepository`

## 4. Endpoints

| Method | Path | Change |
|--------|------|--------|
| GET/POST | `/api/crypto-mi/v1/fx-intel/schedule` | List + upsert enabled/hour/minute/timezone |
| POST | `/fx-intel/signals` | Form fields: kind, sound_profile, condition, value, title, … |
| POST | `/fx-intel/paper` | risk_warnings, idempotency_key, R/R in risk |

## 5. Frontend

- `CryptoOtcDeskPage.tsx` — schedule status, specialist settings panel, signal form, auto-refresh after mutations
- `specialistAndSignalPanels.tsx` — new
- `paperTradingPanels.tsx` — equal green CTAs; R/R field; TV fallbackQuote
- `TradingViewEmbed.tsx` — honest DXY fallback (never swap instrument)
- `cryptoIntelPanels.tsx` — equal result CTAs

## 6. Paper Trading lifecycle

Place (MARKET/LIMIT) → risk preview (Risk $, Risk %, R/R) → Risk Agent soft warning → open position → refresh PnL → manual close / SL / TP → journal. Idempotency key prevents double-submit.

## 7. Analysis scheduler lifecycle

Defaults (overridable): Morning 07:00, Before Europe 07:30, Before USA 15:00, Evening 20:00, TZ default `Europe/Kyiv` but stored/configurable (e.g. America/New_York). Enable → next_run computed; disable → «Автозапуск не настроен». Last result recorded after run.

## 8. Signal lifecycle

Form kinds: price_alert / analysis_result / agent_event / scheduled_event / macro_alert. Sound profiles as identifiers. Lifecycle ACTIVE/DISABLED. Appears after create; list refresh.

## 9. Traceability

analysis_run_id / signal_id auto-linked into paper from query/result; journal retains links; notifications for position opened.

## 10. Миграции

`migrations/versions/a0u123456789_fx_desk_50_5.py` — `fx_mi_desk_configs`, `fx_mi_paper_accounts`, optional `idempotency_key` on paper orders.

## 11–12. Tests

| Suite | Result |
|-------|--------|
| `tests/test_sprint_50_5_operator_desk.py` | PASSED |
| `tests/test_sprint_50_4_analysis_pipeline.py` | PASSED |
| `tests/test_sprint_50_2_operator_desk.py` | PASSED |
| `tests/test_crypto_tx_antifraud_48_0.py` | PASSED |
| vitest `sprint_50_5` + `50_4` | PASSED |

**Pass counts (targeted this sprint):** pytest 34 passed (combined 50.5/50.4/50.2/48.0 run); vitest see session log.

## 13. Known limitations

- Platform cron jobs in Postgres still system-seeded UTC; tenant schedule is desk-layer timezone config (wired for UI/next_run). Full dual-write into `ScheduledJobRepository.create_cron_job` per tenant is deferred.
- Specialist settings primarily localStorage (+ stamped on specialists); DB `fx_mi_desk_configs` table added for durable configs but full hydrate path is PARTIAL.
- Macro provider soft-fail already WAIT via missing_sources; FairEconomy retry/backoff not expanded beyond existing providers.
- Browser TV DXY availability depends on TradingView CDN; fallback is quote-only.

## 14. Data gaps

Honest: macro calendar unavailable → gaps list; DXY TV unavailable → Yahoo quote fallback; quote missing → «Нет актуальной котировки» on market paper.

## 15. URLs

- http://127.0.0.1:8080/health
- http://localhost:5180/
- http://localhost:5180/login
- http://localhost:5180/workspace/crypto

Login: `owner@demo.corp` / `demo`

## 16. Процессы

API + Vite left running after verification (durable Cursor shells). PIDs: API `65611`, Vite listener in `/tmp/ados_web_50_5.pid`. Logs: `/tmp/ados_api_50_5.log`, `/tmp/ados_web_50_5.log`.

### Manual acceptance (API, 2026-08-12)

| Flow | Result |
|------|--------|
| A Evening schedule enable + run | Автозапуск Включён · 20:00 Europe/Kyiv · next 12.08.2026 20:00 · result SELL_BIAS 44% · persist postgres |
| B Create analysis_result signal | appears (signals_count≥1) |
| C Paper LIMIT + R/R | PENDING ok; MARKET open when quote available |
| D Manual close → journal | signal_id + analysis_run_id linked |
| Technical Agent run | ok |

## Status matrix

| Area | Status |
|------|--------|
| Configurable schedule + timezone | DONE |
| Scheduler status UI | DONE |
| Specialist Run/Configure | DONE |
| Specialist settings panels | DONE |
| Risk Agent paper R/R warning | DONE |
| Signal form + kinds + sounds | DONE |
| Chart green CTAs + vertical layout | DONE |
| DXY TV honest fallback | DONE |
| Analysis result CTAs | DONE |
| Idempotency paper | DONE |
| Migration 50.5 | DONE |
| Tests + antifraud | DONE |
| Platform cron dual-write | PARTIAL |
| Full DB hydrate of all desk configs | PARTIAL |

## STOP

Sprint 50.5 complete. **Do not start Sprint 50.6.**
