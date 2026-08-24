# Sprint AGRO 2.1 — Counterparty 360 / CRM / Deals / Contracts / Settlements

## Result

**SPRINT AGRO 2.1 COMPLETE**

Do **not** start AGRO 2.2.

One Agro desk. Existing `/workspace/agro` + `/api/agro-ops/v1`. No second CRM, no new top-level routes, no invented balances.

## Architectural decisions

- **Extend `services/agro_ops`, do not replace.** Mixin `AgroOpsCrmMixin` (`services/agro_ops/crm.py`) on `AgroOpsService`. Storage remains the generic Postgres `agro_ops_records` registry. New kinds `communication`, `note`, `bank_account` need **no SQL migration**.
- **Same API for web and mobile.** `GET /crm/counterparty/{id}` and `GET /crm/deal/{id}` are the 360 endpoints; UI only changes layout (desktop tabs vs compact mobile sections).
- **Health stays AGRO 2.0.** `sprint: agro-2.0`, `ux_version: AGRO_2_0`, `command_center: AGRO_2_0`. Additive `crm_version: AGRO_2_1`.
- **RBAC in backend.** Bank details and AR/AP require `finance`. Manager list masks money. Viewer cannot create. Credit-limit overflow is **WARNING only**, never a silent block.
- **Honest numbers.** Turnover / debt / margin only from real deals, payments, calculations. Missing cost basis → «Себестоимость: нет данных. Маржа: не рассчитана». Empty → «Нет данных». DEMO stays labelled DEMO.

Rejected: a new `platform_*` CRM package, mixing UAH+USD into one total, auto-merge of duplicates, blocking sales on credit limit.

## Acceptance

| Gate | Status |
| --- | --- |
| Counterparty 360 | **PASS** |
| Contacts | **PASS** |
| CRM list/search/filter | **PASS** |
| Deals | **PASS** |
| Deal workflow | **PASS** |
| Contracts | **PASS** |
| Documents | **PASS** (checklist; received requires file or manual confirm) |
| Payments | **PASS** |
| Partial payments | **PASS** |
| Settlement ledger | **PASS** (per-currency; never mixed FX) |
| Receivables aging | **PASS** |
| Tasks/follow-up | **PASS** |
| Communication log | **PASS** (manual only; no fake Telegram/WhatsApp) |
| Duplicate detection | **PASS** (warn; Open existing / Continue with `force`) |
| Import/export | **PASS** (CSV + parsed `rows`; Excel-openable CSV. Native `.xlsx` binary writer not added) |
| Audit | **PASS** (`_activity` actor/time/old/new/source) |
| RBAC backend | **PASS** |
| Desktop | **PASS** |
| Mobile | **PASS** (cards + compact 360 sections, not 11 tiny tabs) |
| Public HTTPS | **PASS** |
| Android Back/deep links | **PASS** (`?view=counterparties&id=` / `?view=deals&id=` pushed; Back clears `id`) |
| Dead buttons | **0** on CRM 360 / list / deal 360 |

Regression (not broken): AGRO 2.0 dashboard, Weather, Prices & Markets, Agro Intelligence, Logistics, Warehouse, Accounting, Tasks, Calendar, Notifications, desktop/mobile nav.

## Tests

- backend **88 passed / 0 failed** (`test_sprint_agro_2_1` + 2.0 + command center + production 1.0 + operations 1.1–1.2 + 1.4–1.9 + live-data 1.3 + weather)
- frontend **56 passed / 0 failed** (`src/web` `workspace/agro`)

## Migrations

None. Same `agro_ops_records`. No sqlite.

## New endpoints

Registered **before** `/{alias}` catch-all:

- `GET /api/agro-ops/v1/crm/list`
- `GET /api/agro-ops/v1/crm/counterparty/{id}`
- `GET /api/agro-ops/v1/crm/deal/{id}`
- `POST /api/agro-ops/v1/crm/deal/{id}/status`
- `GET /api/agro-ops/v1/crm/duplicates`
- `POST /api/agro-ops/v1/crm/import`
- `GET /api/agro-ops/v1/crm/export`
- `POST /api/agro-ops/v1/crm/communication`
- `POST /api/agro-ops/v1/crm/note`
- `POST /api/agro-ops/v1/crm/follow-up`
- `GET /api/agro-ops/v1/crm/analytics`

## URLs

- **DESKTOP URL:** http://127.0.0.1:5180/workspace/agro
- **MOBILE PUBLIC HTTPS URL:** https://logos-philip-environment-determination.trycloudflare.com/workspace/agro

Deep link example: `/workspace/agro?view=counterparties&id=<uuid>`

Temporary Cloudflare tunnel to Vite `:5180` (API `:8080`). Laptop must stay on.

Live probe (this session): public page **200**, public health `crm_version=AGRO_2_1`. Created counterparty + two-role company + contact + deal + partial payment (paid 3000 / remaining 7000) + follow-up task; 360 reopen returned the contact.

## What shipped

1. Multi-role counterparties (farmer, producer, trader, elevator, warehouse, processor, plant, exporter, importer, carrier, forwarder, broker, port, supplier, buyer, other) on **one** record.
2. Counterparty 360 header, quick actions, desktop tabs (Обзор…История) / mobile sections (Обзор / Сделки / Деньги / Документы / Ещё).
3. Legal data + bank accounts hidden without `finance`. Several accounts via `bank_account` kind.
4. Multiple contacts; tap-to-call / email / Telegram / WhatsApp links.
5. Statuses including Проблемный / Чёрный список + optional reason.
6. Tags + CRM filter (type, region, manager, tag, crop, status, debt, overdue, risk). Search name / EDRPOU / phone / email.
7. Crops profile from **actual deals only**.
8. Deal create (buy/sell, qty×price, VAT/schedule/incoterms/places) + Deal 360 + workflow matrix (no silent impossible jumps) + timeline via activity (`USER`/`SYSTEM`/`API`/`IMPORT`/`TELEGRAM`).
9. Contracts + expiry alerts 30/14/7/1 in Важно сегодня, notifications (`evaluate_reminders`), 360.
10. Currency-aware settlements, partial payments, payment schedules, aging buckets, credit-limit **warning**.
11. Manual communication log + follow-up → real task.
12. Manager sees assigned work without company-wide profit. Director operational KPIs (no salesperson leaderboard).
13. Duplicate warn (no auto-merge). CSV import preview-before-commit. Export respects `export`+`finance`.
14. Context-aware quick create: inside a counterparty, deal/payment/shipment/task/document preselect that id.

## Modified files

- `services/agro_ops/crm.py` (new mixin)
- `services/agro_ops/service.py`
- `services/agro_ops/command_center.py`
- `services/agro_ops/desk.py`
- `applications/agro_enterprise/api/ops_handlers.py`
- `applications/agro_enterprise/api/register.py`
- `src/web/workspace/agro/AgroCrmList.tsx` (new)
- `src/web/workspace/agro/AgroCounterparty360.tsx` (new)
- `src/web/workspace/agro/AgroDeal360.tsx` (new)
- `src/web/workspace/agro/AgroBusinessPage.tsx`
- `src/web/workspace/agro/agroLabels.ts`
- `src/web/workspace/business-ops/BusinessCabinetShell.tsx`
- `tests/test_sprint_agro_2_1.py` (new)
- `src/web/workspace/agro/sprint_agro_2_1.test.tsx` (new)

## Unresolved real issues

1. **Native XLSX binary** not written; CSV is the operational import/export (Excel opens it). Client may POST already-parsed `rows` for XLSX.
2. **Channel integrations** (Telegram / WhatsApp / email inbox) are not connected — manual log only, as specified.
3. Command-center notification bell still has no dedicated inbox handler (pre-existing AGRO 2.0; not a new 2.1 dead CRM control).
4. Physical device tap-through at 412×915 was not performed in this session; layout is `useIsMobile` (max-width 767) and public HTTPS loads the same app.

**STOP. Do not start AGRO 2.2.**
