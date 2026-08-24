# AUTO 1.4 COMPLETE

Live private Telegram authorization for Auto OS staff on the **existing** ADOS bot. No second bot. Frozen `/api/auto/v1` unchanged. Agro, Legal, Crypto, Beauty, Travel untouched.

**Workspace:** Рабочее пространство → Авто → Telegram / Настройки (`/workspace/auto?view=telegram`, `/workspace/auto?view=settings`)  
**API:** `/api/auto-ops/v1` (private, org-scoped; AUTO 1.0–1.3 contracts kept, Telegram live routes additive)  
**Bot entrypoint:** `main.py` → `bootstrap.build_dispatcher` → `startup.run_startup` → `dp.start_polling(bot)`  
**Mode:** polling (webhook URL empty)

---

## Completion checklist

| Gate | Result |
|------|--------|
| Private authorization | **PASS** |
| Role menus | **PASS** (director / manager / accountant / admin) |
| VIN search | **PASS** (org-scoped) |
| Vehicles | **PASS** (open + `/status VIN STATUS`) |
| Logistics | **PASS** (`/logistics`, `/container`, `/eta`) |
| Customs | **PASS** (`/customs`, `/vat`, `/broker`) |
| Client CRM | **PASS** (`/client`) |
| Deals | **PASS** (`/deal`, `/sale`) |
| Reservations | **PASS** (409 on second ACTIVE) |
| Payments | **PASS** (accountant/director `/pay`; manager 403) |
| Expenses | **PASS** |
| Documents | **PASS** (`/doc`) |
| Photos | **PASS** (`/photo` + file) |
| Tasks | **PASS** (create + complete) |
| Notifications | **PASS** (outbox + event fan-out) |
| Morning summary | **PASS** (`auto.ops.morning` + `POST /telegram/summaries/morning`) |
| Evening summary | **PASS** (`auto.ops.evening` + `POST /telegram/summaries/evening`) |
| RBAC | **PASS** |
| Tenant isolation | **PASS** (same VIN string, different orgs; one Telegram → one org) |
| Audit | **PASS** (`telegram_member_upserted`, `telegram_<cmd>`) |
| Bot running | **PASS** (single `main.py` poller, no Telegram Conflict) |
| AUTO 1.0–1.3 regression | **PASS** |
| Tests | **59 passed / 0 failed** (backend 45 = AUTO 1.0 ×9 + 1.1 ×8 + 1.2 ×8 + 1.3 ×11 + 1.4 ×9; frontend 14 = 1.0 ×5 + 1.1 ×2 + 1.2 ×2 + 1.3 ×3 + 1.4 ×2) |

---

## Architectural decisions

1. **Reuse the existing ADOS Telegram process. Do not create a second bot.**  
   Staff commands live in `routers/auto_ops_telegram_router.py`, registered immediately after `auto_add_vehicle_router` in `startup.py::BOT_ROUTER_PATHS` and `platform_legacy/adapter.py`. Unbound `/start` is **not** intercepted, so Super App / CRM / marketplace `/start` still works.

2. **Mixin, not a second Auto service.**  
   `AutoOpsTelegramMixin` in `services/auto_ops/telegram.py` on `AutoOpsService`. VIN, logistics, customs, CRM, expenses, receipts, documents, photos, tasks stay in AUTO 1.0–1.3 methods.

3. **Membership is private and one-org.**  
   `telegram_id` binds to one organization + `auto_*` role. A second org for the same Telegram returns 409. Unauthorized slash commands (`/vin`, `/auto`, …) deny; they do not leak into public Super App search.

4. **HTTP inbound is the test/ops double of Telegram, not a public webhook.**  
   `POST /api/auto-ops/v1/telegram/inbound` drives the same `handle_telegram_inbound` used by the aiogram router. Pytest never calls Telegram HTTP.

5. **Callbacks are owned.**  
   Inline buttons use `ao:` tokens stored with the Telegram user who received them. Another staff member pressing the same button gets 403.

6. **Mutating commands are idempotent.**  
   Repeat `/expense`, `/pay`, `/task`, `/photo`, `/doc`, `/reserve`, `/status` with the same text returns `duplicate: true`.

7. **Copy stays honest for AUTO 1.0 UI tests.**  
   Live message still contains «Новый бот не строится». The desk never says «бот подключён и работает».

Rejected: a new Telegram bot; intercepting unbound `/start`; putting staff ops on frozen `/api/auto/v1`; starting AUTO 1.5.

---

## 1. Actual Telegram entrypoint

Canonical process:

1. `main.py` (`asyncio.run(main())`)
2. `bootstrap.py` — `bot = Bot(token=BOT_TOKEN)`, `build_dispatcher`
3. `startup.run_startup()` — routers via `platform_legacy.legacy.telegram.register_bot_routers(dp)` (list in `startup.py::BOT_ROUTER_PATHS`)
4. `dp.start_polling(bot)` after `note_telegram_mode(mode="polling")`

Do not start a second `main.py`. If `:8080` is already taken by this process, do not also run `scripts/run_api_local.py`.

---

## 2. Exact safe startup commands

Frontend (Vite `:5180`, already used for this sprint):

```bash
cd src/web && npm run dev
```

Bot + API together (preferred local stack for AUTO 1.4):

```bash
cd /Users/macbook/Desktop/TelegramBotCourse
ENVIRONMENT=development REDIS_REQUIRED=false .venv/bin/python main.py
```

API-only (no bot) — use **only** when `main.py` is not running:

```bash
ADOS_SKIP_MIGRATIONS=1 ENVIRONMENT=development REDIS_REQUIRED=false .venv/bin/python scripts/run_api_local.py
```

Checks (no token printed):

```bash
curl -sS http://127.0.0.1:8080/api/auto-ops/v1/health
curl -sS -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:5180/workspace/auto?view=telegram"
pgrep -fl 'python main.py'
```

Bind a private test user (director), then `/start` in Telegram:

```bash
curl -sS -X POST http://127.0.0.1:8080/api/auto-ops/v1/telegram/members \
  -H "X-Organization-Id: YOUR_ORG" -H "X-Role: auto_director" \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": YOUR_TELEGRAM_ID, "role": "auto_director", "label": "Test director"}'
```

---

## 3. Polling / webhook mode

**polling.** `getWebhookInfo` reported webhook URL empty, `pending_updates=0`. Aiogram log: `Start polling` / `Run polling for bot`. Platform webhook *handlers* (CRM / integrations) still register; they are not the Telegram bot transport.

---

## 4. Bot health (this session)

| Item | Value |
|------|--------|
| Process | single `python main.py` |
| Duplicate poller | none (no Telegram Conflict) |
| Transport | polling |
| API | `GET /health` HTTP 200; `GET /api/auto-ops/v1/health` sprint `AUTO_1.4`, telegram `live` |
| Frontend | `GET /workspace/auto?view=telegram` HTTP 200 |
| Duplicate API | standalone `run_api_local.py` stopped so only `main.py` listens on `:8080` |

Admin bot status (`GET /telegram/status`, director/admin only): mode, last successful update, last error, authorized users, notifications sent today. Web: Настройки, `data-testid="auto-telegram-bot-status"`.

---

## 5. Authorized-role test results

| Actor | Result |
|-------|--------|
| Unauthorized Telegram user | 403 deny on `/vin` and `/auto`; `/start` not stolen from the rest of the bot |
| Director | menu with VIN / logistics / report / bot status; VIN; vehicle status; report; summaries |
| Manager | menu without payments; expense / task / photo / doc; `/pay` 403 |
| Accountant | `/pay` confirmed; menu with payments/report; `/botstatus` 403 |
| Callback theft | other staff 403 |
| Duplicate expense | `duplicate: true`, same item id |
| Tenant | same VIN string → different vehicles per org; second-org bind 409 |

---

## 6. Changed files

### Backend
- `services/auto_ops/telegram_auth.py` — parse, menus, intercept (not `/start`), callback token, idempotency, RBAC per command
- `services/auto_ops/telegram.py` — members, inbound, VIN/logistics/customs/CRM/expense/pay/task/photo/doc/reserve/status/report, outbox, summaries, bot status
- `services/auto_ops/telegram_boundary.py` — sprint AUTO 1.4, `implemented: True`, live copy
- `services/auto_ops/service.py` — mixin, bag keys, dashboard sprint AUTO 1.4, test reset
- `services/auto_ops/crm.py` — Telegram fan-out from CRM notifications
- `services/auto_ops/rbac.py` — unchanged roles (director / accountant / manager / admin)
- `routers/auto_ops_telegram_router.py` — `AutoOpsBound` + `AutoOpsSlash`, prefix `ao:`
- `applications/auto_enterprise/api/telegram_handlers.py` — status / members / inbound / summaries
- `applications/auto_enterprise/api/register.py` — live Telegram routes
- `applications/auto_enterprise/config.py` — sprint `AUTO_1.4`, version `1.4.0`
- `repositories/auto_ops_repository.py` — `telegram_member` / `telegram_outbox`
- `database/models/auto_ops.py` — `AutoOpsTelegramMember`, `AutoOpsTelegramOutbox`
- `migrations/versions/n3i456789012_auto_ops_1_4.py`
- `startup.py` — router path after add-vehicle
- `platform_legacy/adapter.py` — `include_router(auto_ops_telegram_router)`
- `main.py` — `note_telegram_mode(mode="polling")` before `start_polling`
- `services/pg_scheduler_engine.py` — jobs `auto.ops.morning` / `auto.ops.evening` (file also contains prior uncommitted FX/Legal/Agro jobs)

### Frontend
- `src/web/workspace/auto/AutoBusinessPage.tsx` — live Telegram copy; admin bot status in Настройки

### Tests
- `tests/test_auto_ops_1_4.py`
- `src/web/workspace/auto/sprint_auto_1_4.test.tsx`
- `tests/test_auto_ops_1_0.py` / `_1_1.py` / `_1_2.py` / `_1_3.py` — accept sprint AUTO 1.4 + live telegram
- `tests/test_telegram_ai_super_app_43_0.py`, `tests/test_hotfix_46_2_2_add_car_vin_fsm.py` — Super App still after Auto ops router (`.index()`, not `[1]`)

### Docs
- `docs/SPRINT_AUTO_1_4_RESULT.md`

---

## 7. Migrations

Additive Alembic revision `n3i456789012` revises `m2h345678901`:

- `auto_ops_telegram_members`
- `auto_ops_telegram_outbox`

**Local DB this session:** `alembic_version` is `i8d901234567` (separate head). AUTO tables including vehicles are absent locally; the desk uses the existing **postgres + memory fallback** (same as AUTO 1.0–1.3 here). `alembic upgrade head` still fails on older AUTO 1.1–1.3 `information_schema` checks that pass `%s` to asyncpg. Do not treat that as an AUTO 1.4 regression.

---

## 8. API / routes

Prefix `/api/auto-ops/v1` (all private, org-scoped):

| Method | Path | Notes |
|--------|------|--------|
| GET | `/telegram` | Boundary (now live) |
| GET | `/telegram/status` | Admins/directors only |
| GET/POST | `/telegram/members` | Bind `telegram_id` + role; actor role from headers, not body |
| POST | `/telegram/inbound` | Test/ops inbound (`telegram_id`, `text`, `extra`, `callback_data`) |
| POST | `/telegram/summaries/{morning\|evening}` | Admin |

Staff commands (inbound `text` or live bot): `/start` `/auto` `/vin` `/logistics` `/container` `/eta` `/customs` `/vat` `/broker` `/client` `/deal` `/sale` `/expense VIN amount CATEGORY` `/pay VIN amount` `/task VIN title` `/photo VIN` `/doc VIN type` `/reserve VIN client_id` `/status VIN STATUS` `/report` `/botstatus`

---

## 9. Web settings route

`/workspace/auto?view=settings` — Telegram card + admin-only bot status (mode, last update, last error, authorized users, notifications today).  
`/workspace/auto?view=telegram` — live staff copy; «Новый бот не строится».

---

## 10. Known limitations

- Live Telegram file download for photos needs the running bot session; pytest uses `content_base64`.
- Morning/evening summaries write the org outbox (deduped per day). Push to Telegram HTTP is the bot answering on the next interaction / future delivery worker — AUTO 1.5 territory.
- Local AUTO SQL tables are not on the current alembic head; memory fallback is active.
- Platform `/health` may show `degraded` when Redis is optional; Auto ops health is independent (`AUTO_1.4` / live).
- Manager cannot confirm `/pay` or create `PURCHASE` expenses (finance_write). Use STORAGE/OTHER for manager Telegram expenses.
- Unbound users still get the existing ADOS `/start`. Only bound staff see Auto OS menu.

---

## 11. What is ready for AUTO 1.5

Do **not** start AUTO 1.5 in this sprint. Natural follow-ups:

- Deliver outbox rows to Telegram (sendMessage) without a second bot
- Optional webhook transport + duplicate-poller guard in ops
- Admin UI to bind/unbind Telegram members (API already exists)
- Apply `n3i456789012` on the production alembic chain once AUTO 1.1–1.3 `%s` checks are fixed
- Bank / acquiring confirmation still not live (AUTO 1.3 leftover)

STOP AFTER AUTO 1.4. DO NOT START AUTO 1.5.
