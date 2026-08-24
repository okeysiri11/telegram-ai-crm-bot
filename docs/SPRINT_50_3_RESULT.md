# Sprint 50.3 — RESULT

## Scope

Crypto operator desk completion: signal notifications, real calendar UI, paper demo account + order engine, journal/traceability, cross-links, Russian UI honesty, localhost stack scripts. **No Sprint 50.4. No real broker. No Telegram/email delivery required.**

## AUDIT OF 50.2

| Item | Status |
|------|--------|
| Dual charts + paper/journal shell | DONE (50.2) |
| Paper statuses lowercase inconsistency | FIXED in 50.3 → `DRAFT/PENDING/OPEN/CLOSED/CANCELLED` |
| Calendar = macro list only | FIXED → month/week/day UI + filters |
| Notifications = channel table stub | FIXED → in-app lifecycle + actions |
| Paper account 100k demo | DONE |
| Independent chart timeframes | DONE |
| Stack scripts silent/fragile exit | HARDENED |

## VERTICAL CHARTS

**DONE** — `DualChartsPanel` default `layout="vertical"`; EUR/USD and DXY stacked with independent timeframe controls.

## MY INSTRUMENTS

**DONE** — watchlist nav «Мои инструменты»; persistence via `otcPrefs` + primary/comparison chart prefs (`loadChartInstrumentPrefs`).

## ANALYSES

**DONE** (carried + linked) — Run Now presets, settings toggles, cross-link to signals/paper/calendar.

## AI SPECIALISTS

**DONE** (carried + linked) — Run Now / Настроить; Technical / Macro / News Agent names retained; Russian actions.

## CHIEF ANALYST

**DONE** (carried) — consensus structured fields from 50.2; Chief in specialist list; links into signal → paper flow.

## SIGNALS

**DONE** — create from chart; lifecycle field on manual signals; price triggers evaluate on paper refresh; Signal Center + notifications.

## SIGNAL NOTIFICATIONS

**DONE** — statuses `ACTIVE | TRIGGERED | ACKNOWLEDGED | EXPIRED | DISABLED`; in-app panel; actions Подтвердить / Открыть / Отключить; optional browser beep when `Notification.permission === granted`. Telegram/email **not** required (explicit).

## CALENDAR

**DONE** — Месяц / Неделя / День; ← Сегодня →; real dates; category filters (Макроэкономика, Новости, Анализы, AI-специалисты, Сигналы, Сессии, Paper Trading, Ручные); day drawer fields; manual event form; aggregate API `GET/POST /fx-intel/calendar`.

## PAPER TRADING

**DONE** — section «Бумажная торговля»; demo account `100000 USD`; metrics Баланс / Equity / Open P&L / Realized P&L / open positions / win rate / trades; form MARKET/LIMIT + SL/TP + risk preview; backend quote only (no TradingView DOM scrape).

## PAPER ORDER ENGINE

**DONE** — statuses + market/limit/SL/TP/manual close/cancel pending; unrealized/realized PnL; persist best-effort via existing `FxMarketIntelRepository` when DB available, in-memory always.

## JOURNAL

**DONE** — columns + filters + row details with why/signal/analysis/agent/confidence/result; `training_enabled: false`.

## CROSS LINKS

**DONE** — chart → signal → analysis → agents → Chief → signal → paper → journal → calendar/notifications via `CrossLinkBar` + calendar event links + `/fx-intel/links`.

## PERSISTENCE

**PARTIAL** — in-memory desk ops always; Postgres persist for signals/paper/journal when session available (same pattern as 50.2). Chart/instrument prefs in `localStorage`. No new migration required for notifications/calendar (memory-first).

## UI CLEANUP / DATA HONESTY

**DONE** — Russian operator labels; honesty states Подключено / Нет данных / Источник недоступен / Данные устарели / Частичные данные / Требуется настройка; timestamps/providers shown on quotes where present. Telegram/email not forced in notifications panel.

## TESTS

| Suite | Result |
|-------|--------|
| `tests/test_sprint_50_3_operator_desk.py` | PASSED (runtime) |
| `tests/test_sprint_50_2_operator_desk.py` | PASSED (uppercase statuses) |
| `tests/test_crypto_tx_antifraud_48_0.py` + `test_crypto_payout_orchestrator_48_1.py` | PASSED |
| `src/web/.../sprint_50_3_operator_desk.test.ts` (+ 50.0/50.2) | PASSED (19 tests) |

## LOCALHOST

Scripts: `scripts/run_fx_intel_stack.sh`, `scripts/stop_fx_intel_stack.sh` — reclaim own listeners, wait `/health` + frontend 200, print URLs, keep logs under `/tmp/ados_*_50_3.log`, non-zero exit if not ready.

Runtime verification recorded in this session after stack start (see checklist below).

## Architectural decisions

1. **Extend `services/fx_market_intel/`** (notifications, calendar_events, desk_ops, paper_trading) — no new `platform_*` package.
2. **UPPERCASE paper statuses** — canonical; accept lowercase on fill/cancel for compat.
3. **Calendar aggregation in desk_ops** — single bundle endpoint; UI owns month/week/day rendering.
4. **Notifications in-memory** — sufficient for operator demo; channels other than in-app deferred.

## KNOWN DEBT

- Calendar AGENT category sparsely populated (specialist runs mainly appear as ANALYSIS).
- Browser Notification permission + sound depend on user gesture / HTTPS policy in some browsers.
- Full `npm run lint` still reports pre-existing errors outside this sprint (`ai-command`, `hercules`, `chartProvider` erasableSyntaxOnly).
- Paper equity model is demo ledger (not broker margin).
- Postgres notification/calendar tables not added (memory-first).

## STOP CONDITION

Sprint 50.3 finished. **Sprint 50.4 not started.**

## Runtime checklist (verified 2026-08-11)

| URL | Expected | Verified |
|-----|----------|----------|
| `http://127.0.0.1:8080/health` | 200 | **200** |
| `http://localhost:5180/` | 200 | **200** |
| `http://localhost:5180/login` | reachable | **200** |
| `http://localhost:5180/workspace/crypto` | reachable | **200** |
| `/api/crypto-mi/v1/fx-intel/health` | 200 | **200** |
| `/fx-intel/calendar` | 200 | **200** |
| `/fx-intel/paper` (account 100k) | 200 | **200** |
| `/fx-intel/notifications` | 200 | **200** |

Services left running (API PID in `/tmp/ados_api_50_3.pid`, Vite in `/tmp/ados_web_50_3.pid`). Logs: `/tmp/ados_api_50_3.log`, `/tmp/ados_web_50_3.log`.
