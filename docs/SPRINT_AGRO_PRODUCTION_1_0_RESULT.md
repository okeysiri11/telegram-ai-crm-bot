# SPRINT AGRO PRODUCTION 1.0 — RESULT

## STATUS

**COMPLETE** as a production-handover workspace on the existing AGRO vertical.

No second AGRO application was created. Marketplace/enterprise in-memory APIs were left intact.
Pilot workflow moved to `/workspace/agro/pilot`.

## AUDIT (before implementation)

| Area | Finding |
|------|---------|
| Already works | `services/agro_ops` durable desk (CRUD, finance calc, intel honesty, files, RBAC, dashboard); Postgres `agro_ops_records`; marketplace/enterprise in-memory APIs; Telegram trading (partial) |
| Partial | No HTTP `/api/agro-ops/v1`; no production web desk; no agro scheduler jobs; no agro_ops tests |
| Fake/demo | `AgroStore` / `AgroEnterpriseStore` (in-memory); vertical catalog demo stats; Telegram stubs |
| Reused | Legal Ops pattern (handlers + BusinessCabinetShell + file blobs + RBAC permissions + pg_scheduler); existing auth/tenant |

## DONE

- AGRO home / command center with KPI cards and onboarding
- Counterparty registry (multi-role) + contacts + dossier drawer
- Deals, contracts, crops (custom quality attributes), shipments, warehouses
- Document attachments (disk blob, not base64-in-DB) with paperclip upload
- Deal economics calculator (Decimal, FX never invented)
- Accounting view (invoices/payments/receivables/payables + CSV export)
- RBAC: `agro_director` / `agro_accountant` / `agro_manager` / `agro_observer`
- Audit log (safe before/after)
- Агро-разведка: provider catalog, morning/evening/weekly/outlook, agents, ask-AI
- Honest freshness: LIVE / DELAYED / STALE / NOT_CONFIGURED / UNAVAILABLE
- Notifications (in-app always; Telegram/email only if configured)
- Calendar + tasks
- Settings (roles, sources, channels)
- Handover onboarding: «Добро пожаловать в Агро» + «Что здесь делать?»
- Scheduler jobs `agro.intel.morning` / `agro.intel.evening` (idempotent per org/day)

## PARTIAL

- Map / GIS / satellite: not in this sprint (existing precision-ag APIs remain demo)
- Inline dossier editing: open/view + create forms; full field edit via API
- Calendar Month/Week/Day visual board: list + create (Legal calendar board not duplicated)
- Weekly/outlook scenarios are qualitative until official sources are connected

## NOT CONFIGURED

All official/market/weather providers except **manual import**:

- Минагрополитики, Госстат, Укргидрометцентр, таможня, порты
- USDA/WASDE (минсельхоз США), ФАО, Еврокомиссия, Евростат, AMIS, Всемирный банк
- Licensed market prices, weather provider, FX rates

UI status: **«Требуется подключение источника»**. Nothing is fabricated.

## EXTERNAL CREDENTIALS REQUIRED

To go live with external intelligence:

- Official/licensed API keys or RSS/open-data agreements for the providers above
- Optional: `TELEGRAM_BOT_TOKEN` / `BOT_TOKEN` for Telegram notifications
- Optional: `SMTP_HOST` or `EMAIL_SMTP_HOST` for email notifications
- Optional FX provider (until then calculator shows «Курс не подключён»)

## DATABASE / MIGRATIONS

Existing only: `migrations/versions/i8d901234567_agro_ops_1_0.py` → table `agro_ops_records`.
No new migration required.

## ENDPOINTS (`/api/agro-ops/v1`)

- `GET /health` `GET /roles` `GET /catalogs` `GET /dashboard`
- `GET|POST /entities/{kind}` `GET /entities/{kind}/{id}` `GET .../related` `POST ...` `POST .../archive|restore`
- Aliases: `/counterparties` `/deals` `/contracts` `/calculations` `/payments` `/shipments` `/tasks` `/calendar` `/notifications` `/activity` …
- `POST /calculations/preview` `GET /finance/summary` `GET /export/{invoices|payments|calculations}`
- `GET|POST /files` `GET /files/{id}/content` `POST .../rename` `POST .../link`
- `GET /providers` `POST /intel/import` `GET /reports` `POST /reports/generate` `POST /agents/run` `POST /ai/ask`
- `GET /channels`

## UI ROUTES

- http://127.0.0.1:5180/workspace/agro — production desk
- `?view=counterparties|deals|contracts|documents|calculations|accounting|shipments|crops|markets|intel|calendar|tasks|notifications|settings`
- http://127.0.0.1:5180/workspace/agro/pilot — previous live-workflow page (preserved)

## ROLES

| Role | Can | Cannot (default) |
|------|-----|------------------|
| AGRO_DIRECTOR | all AGRO data, approve deals, margins, intel admin, delete companies | — |
| AGRO_ACCOUNTANT | view counterparties/contracts, invoices/payments, attachments, export | delete companies, approve deals, generate intel, change sources |
| AGRO_MANAGER | create/edit ops, intel, AI | admin / delete companies |
| AGRO_OBSERVER | view | mutate |

## PROVIDERS

Interface catalog only. Connected today: **manual_import** (LIVE). All others NOT_CONFIGURED.

## SCHEDULER JOBS

- `agro.intel.morning` — cron `0 5 * * *` UTC ≈ 08:00 Europe/Kyiv
- `agro.intel.evening` — cron `0 15 * * *` UTC ≈ 18:00 Europe/Kyiv
- Deduplicated: one report per (org, kind, date)

## TESTS

- Backend `tests/test_sprint_agro_production_1_0.py`: **12 passed**
  (CRUD, contacts, calc math, attachments, RBAC, tenant isolation, honest providers, intel dedupe, scheduler idempotency, audit, notifications, AI DATA GAP)
- Frontend `workspace/agro/sprint_agro_production_1_0.test.tsx`: **3 passed**
- Regression: Lawyer 3.6 + cabinets + agro marketplace: **21 passed**

## REMAINING PRODUCTION BLOCKERS

1. Connect at least one official price/harvest/weather source (license/agreement).
2. Configure Telegram/email if operators need off-app alerts.
3. Confirm Postgres is reachable in the target environment (memory fallback works, but handover should use DB).
4. Do not treat marketplace/enterprise in-memory APIs as the production desk.

## LOCAL START / STOP

```bash
# start
.venv/bin/python scripts/run_api_local.py          # http://127.0.0.1:8080
cd src/web && npm run dev                          # http://127.0.0.1:5180

# stop
Ctrl+C in each terminal
```

Health: http://127.0.0.1:8080/api/agro-ops/v1/health

## MANUAL ACCEPTANCE URLS

1. Login as director → http://127.0.0.1:5180/workspace/agro
2. Контрагенты → создать «Test Agro Partner» (farmer+supplier) → контакт → 📎 договор PDF
3. Сделки → закупка пшеницы 100 т → Расчёты → транспорт/хранение → сохранить
4. Оплата + поставка
5. Агро-разведка → утренний/вечерний обзор (только внутренние + ручной импорт)
6. Сменить роль на бухгалтера → бухгалтерия доступна; удаление компании и генерация обзора запрещены
7. Обновить страницу — данные на месте (Postgres) / память процесса (если БД недоступна)

## ARCHITECTURAL DECISIONS

- **Extended `services/agro_ops` + `applications/agro_enterprise`** instead of a new app.
- **Generic `agro_ops_records` JSONB registry** already existed; no parallel typed tables.
- **Intelligence never fabricates**: empty sections stay NOT_CONFIGURED.
- **Pilot page preserved** at `/workspace/agro/pilot` so Sprint 31.1 workflow is not deleted.

## RU LOCALIZATION PASS

User-facing AGRO desk, nav, and pilot copy is Russian:

- Welcome «Добро пожаловать в Агро»; roles «Директор / Бухгалтер / Менеджер / Наблюдатель»
- Statuses, document types, quality attributes, intel bias/confidence in Russian
- Counterparty roles as checkboxes (Фермер, Поставщик…), not `farmer,supplier`
- Attach file: object type + existing object name, not raw ID
- Nav: «Агро», «Товары (закупка / продажа)», «ИИ-помощник»
- Pilot page `/workspace/agro/pilot` chrome and step labels in Russian

Internal IDs, API paths, and Telegram entry aliases (`🌾 Agro Trading`) are unchanged.

## NEXT RECOMMENDED SPRINT

**AGRO 1.1** — connect the first real official feed (USDA WASDE and/or UA open data / RSS), inbound conflict UX for intel items, visual calendar board, and counterparty inline edit in the dossier.

STOP AFTER AGRO PRODUCTION 1.0.
