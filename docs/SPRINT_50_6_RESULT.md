# Sprint 50.6 RESULT — Paper trading durability & lifecycle

**Status:** COMPLETE  
**Date:** 2026-08-12  
**Do not start Sprint 50.7.**

---

## 1. Root cause of the disappearing paper trade

Paper trades were written to Postgres (`save_paper_order` / `save_paper_position` / `save_journal_entry`) but **never hydrated back into process memory** on `GET /paper` or after API restart.

`FxDeskOps` kept orders/positions/journal only in in-memory dicts. After process recycle (or a fresh request context that missed memory), the UI showed an empty desk even though rows existed in DB. Persist also always **INSERT**ed, with no upsert-by-key.

**Fix:** `ensure_hydrated(tenant)` loads payload JSON from DB into memory (once per tenant per process); persist uses **upsert** by `order_key` / `position_key` / `journal_key`.

---

## 2. Files changed

| Area | Files |
|------|--------|
| Desk ops | `services/fx_market_intel/desk_ops.py` |
| Paper / risk | `services/fx_market_intel/paper_trading.py` |
| Journal | `services/fx_market_intel/journal.py` |
| Repository | `repositories/fx_market_intel_repository.py` |
| API | `applications/crypto_enterprise/api/fx_intel_handlers.py` |
| UI | `src/web/workspace/crypto/paperTradingPanels.tsx`, `CryptoOtcDeskPage.tsx` |
| Tests | `tests/test_sprint_50_6_paper_persist.py`, `src/web/workspace/crypto/sprint_50_6_paper_trading.test.tsx` |
| Regression tweaks | `tests/test_sprint_50_2_operator_desk.py`, `tests/test_sprint_50_3_operator_desk.py` (FILLED status) |
| Docs | `docs/SPRINT_50_6_RESULT.md` |

---

## 3. DB models / migration

No new migration in 50.6. Reuses existing Sprint 50.2/50.5 tables:

- `fx_mi_paper_orders`
- `fx_mi_paper_positions`
- `fx_mi_journal_entries`
- `fx_mi_paper_accounts` (account aggregates still primarily in-process; reconstructed from journal on hydrate when needed)

Repository additions: `list_paper_*`, `list_journal_entries`, `upsert_paper_*`, `upsert_journal_entry`.

---

## 4. Endpoints

Prefix: `/api/crypto-mi/v1/fx-intel`

| Method | Path / action | Notes |
|--------|----------------|-------|
| GET | `/paper` | Hydrate → refresh marks/SL-TP → account, orders, positions, journal |
| POST | `/paper` `action=place` | 201 on success; **400** with `message_ru` on failure |
| POST | `/paper` `action=close` | Manual close + journal + notification |
| POST | `/paper` `action=refresh` | Limit fills + SL/TP check; returns full desk payload |
| POST | `/paper` `action=cancel` | Pending/draft cancel |
| POST | `/paper` `action=risk_preview` | Risk / R/R preview |
| GET | `/journal` | Hydrated journal items |
| GET | `/notifications` | Includes paper lifecycle titles |

---

## 5. Lifecycle implemented

1. MARKET place → order **FILLED**, position **OPEN**
2. Journal event **PAPER_POSITION_OPENED**
3. In-app notification «Бумажная сделка … открыта»
4. Lists show order + open position
5. Refresh / GET reloads from memory (+ hydrate from DB after restart)
6. Manual close → position **CLOSED**, journal **PAPER_POSITION_CLOSED**, account trades/realized updated
7. Notification «Бумажная позиция … закрыта. P&L: …»

Idempotency: `idempotency_key` / `client_request_id` replay protected in memory (restored from order payload on hydrate).

---

## 6. Risk calculation

`risk_preview` + `validate_sl_tp_vs_side`:

- BUY: SL below entry, TP above entry
- SELL: inverse
- Potential loss/profit, risk %, reward_risk (R/R)
- Risk Agent soft warnings unchanged (`strict` can block)

---

## 7. Source linking

Optional linkage fields (not raw DB-only IDs):

- `signal_id`, `analysis_run_id`, `agent_result_id`
- Journal/notification `links` → `?view=paper` / `?view=journal`

---

## 8. Journal logic

| Event | When |
|-------|------|
| `PAPER_POSITION_OPENED` | MARKET fill or LIMIT fill |
| `PAPER_POSITION_CLOSED` | Manual close or SL/TP on refresh |

---

## 9. Notifications (in-app only)

Examples shipped:

- «Бумажная сделка EUR/USD открыта»
- «EUR/USD достиг Stop Loss» / «… Take Profit» (on refresh SL/TP close)
- «Бумажная позиция EUR/USD закрыта. P&L: …»

No Telegram/email in this sprint.

**SL/TP auto-trigger:** runs on GET/refresh mark poll only (`sl_tp_auto_trigger.mode=on_refresh`). Aggressive background worker **deferred** (`background_deferred=true`). Manual open/close is fully working.

---

## 10. Acceptance evidence (live local stack)

Authenticated HTTP lifecycle **A–L** against `http://127.0.0.1:8080` — **ACCEPTANCE_OK**.

After API process restart, hydrate still returned the same order/journal IDs — **HYDRATE_OK**.

### One real paper trade

| Field | Value |
|-------|--------|
| order ID | `po_acb54fdf20d1` |
| position ID | `pp_a3cb538b9c5a` |
| instrument | EUR/USD |
| side | BUY |
| entry | 1.1537 |
| SL | 0.5 |
| TP | 5.0 |
| risk | potential_loss 0.6537 · risk_pct 0.001% |
| R/R | 5.884 |
| order status | FILLED |
| journal open ID | `jn_143204a17f92` (`PAPER_POSITION_OPENED`) |
| close | CLOSED · P&L 0.0 |
| journal close ID | `jn_1bc2a292c731` (`PAPER_POSITION_CLOSED`) |
| notifications | open + close titles observed |

Evidence file: `/tmp/sprint_50_6_e2e_evidence.json`

---

## 11. Tests

**Backend**

- `tests/test_sprint_50_6_paper_persist.py` — SL/TP validation, FILLED+open journal, place/close, hydrate merge, RU errors
- Regression: `test_sprint_50_5`, `50_3`, `50_2` paper status updates; Sprint 48 antifraud suites green when run with 50.6

**Frontend**

- `sprint_50_6_paper_trading.test.tsx` — submit → create payload, refresh hook, error display, open position, FILLED order, journal event, close call, no raw DB ID inputs, «Открываем…» + double-submit guard

**Live E2E:** mandatory HTTP A–L passed (not unit-only).

---

## 12. Remaining debt

- Background SL/TP worker still deferred (on-refresh only)
- Paper account row upsert to `fx_mi_paper_accounts` not fully dual-written every tick (aggregates reconstructed / in-memory)
- Specialist settings still largely localStorage (50.5 debt)
- Schedule UI vs Postgres `ScheduledJobRepository` dual-write incomplete (50.5 debt)

---

## 13. Localhost status

Left running for manual verification (do not stop):

| URL | Expected |
|-----|----------|
| http://127.0.0.1:8080/health | 200 |
| http://localhost:5180/ | 200 |
| http://localhost:5180/login | 200 |
| http://localhost:5180/workspace/crypto | 200 |

Logs: `/tmp/ados_api_50_6.log`, `/tmp/ados_web_50_6.log`

Demo login: `owner@demo.corp` / `demo` → Paper view → open / refresh / close.

---

## Architectural decisions

1. **Extend `FxDeskOps` + repository** — no new platform package; paper remains simulation-only (`paper=True`, `trade_execution=False`).
2. **Hydrate-once per tenant** — avoids aggressive DB polling; memory stays source of truth within a process after load.
3. **Upsert by business key** — prevents duplicate rows on re-persist after refresh/close.
4. **FILLED vs OPEN** — filled orders use `FILLED`; open exposure stays on positions (`OPEN`).
5. **SL/TP background deferred** — reuse existing refresh path; no new aggressive scheduler job.
